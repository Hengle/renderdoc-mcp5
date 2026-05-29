# Shader Restoration And Naming

Use this reference when `reverse-action` needs readable HLSL restoration, material/property naming, GBuffer or HGBuffer channel semantics, or AssetRipper metadata cross-checks.

Target: with a RenderDoc capture, restore HLSL that is readable, verifiable, and not over-named. Metadata is optional acceleration, not a requirement.

## Core Rules

1. Preserve decompiled behavior first; rename only after evidence supports it.
2. Require evidence for high-level semantics: metadata, runtime cbuffer values, producer/consumer data flow, RenderDoc exports, or shader-edit probes.
3. Treat metadata as a candidate source only. Metadata can prove the material has a property, but cannot by itself prove `CB2[x].y` equals that property.
4. Prefer capture runtime bindings and cbuffer values over metadata defaults.
5. Keep low-level names for uncertain semantics. Do not force BRDF or material names before the data flow is proven.
6. Do not downgrade to a broad inventory report just because metadata is missing. When metadata is absent, keep the same restoration flow and replace metadata evidence with image, producer/consumer, and probe evidence.

## Required Artifact Layout

For `reverse-action`, the working directory should contain at least:

```text
eid_<eid>_<stage>_<name-or-sid>.hlsl
eid_<eid>_<stage>_<name-or-sid>.annotated.hlsl   or   .notes.md
Action_Restore_Report.md
assets/
debug_shaders/
review/
review/needs_human_review.md
```

Use predictable names. Keep raw decompiler output and annotated output side by side.

## Restoration Order

### 1. Freeze The Decompiled Baseline

- Keep the original Ruri or SPIRV-Cross output, for example `eid_13525_ps_ruri.hlsl`.
- Create an annotated sibling, for example `eid_13525_ps_annotated.hlsl`.
- Start with behavior-preserving cleanup only:
  - merge obvious same-source scalars into `float2` or `float3`
  - keep expression structure; do not algebraically simplify bit packing
  - keep uncertain resources as `CBx_m0[y]`, `Tn`, `Sn`, `Un`

### 2. Build The Action And Resource Chain

Confirm from RenderDoc:

- current draw or dispatch id, shader stage, and output targets
- SRV, CBV, sampler, UAV, VB, and IB bindings
- output RT ResourceId, format, and dimensions
- whether downstream passes read those outputs

Record evidence in this shape:

| Field | Example |
| --- | --- |
| Producer | `eid 13525` HGBuffer PS |
| Output | `SV_Target_4` / RT4 / `ResourceId::212319` |
| Consumer | `eid 14487` / `t21` / `GBufferBaseColorTexture` |
| Format | `R8G8B8A8_SRGB` |
| Confirmed semantics | `rgb` base color/tint, `a` local-vertex-position fade mask |

### 3. Generate Candidate Names From Metadata When Available

Extract from AssetRipper metadata when present:

- property name, type, default value, and description
- shader keywords
- pass tags, LightMode, and render state
- texture properties and channel descriptions

Use these as candidates only:

- `_NormalMap` metadata saying `normal RG / roughness B / MaskA` can help confirm channel semantics
- `_SubsurfaceIntensity` and `_Transmission` existing in metadata does not prove the current variant uses them
- hidden properties such as `_ShadingModel` are reference hints, not a replacement for data-flow proof

If metadata is not available, skip this stage and continue with the rest of the flow. Do not reduce the report quality target.

### 4. Cross-check Runtime Cbuffers

When metadata gives a candidate property but code only has `CB2[x].y`, read the capture's actual cbuffer.

Example evidence:

```text
RenderDoc read_buffer, eid 13525, PS b2:
CB2[2].y = 0.5   -> _SubsurfaceIntensity
CB2[2].z = 0.25  -> _Transmission
CB2[3].z = 0.088 -> _MaskOnDiffuse
CB2[3].w = 1.0   -> _MaskOnTransmission
```

Promote a low-level CB name to a material property only when runtime value, metadata property group, and code-use position all line up.

Without metadata, runtime cbuffer still matters. Use it to:

- identify repeated scalar groups
- compare values against image behavior
- determine whether a channel is likely a normalized mask, threshold, tint, or intensity control

### 5. Trace Producer And Consumer

For GBuffer-like passes, inspect both write side and read side.

Producer-side example:

```hlsl
SV_Target_2.w = float(packedSubsurface5Bits & 3u) / 3.0f;
SV_Target_2.xy = ...;
SV_Target_4.w = ...;
```

Consumer-side example:

```hlsl
float4 gbufferPackedMaterial = GBufferPackedMaterialTexture.Load(...);
uint matX10 = uint(gbufferPackedMaterial.x * 1023.0f);
uint matY10 = uint(round(gbufferPackedMaterial.y * 1023.0f));
```

Write conclusions as channel and bit layout, not vague labels:

```text
RT2.x low3 + RT2.w low2 = round(31 * _SubsurfaceIntensity)
RT2.x high7 = _Transmission-derived packed value
RT2.y low3 = constant 4, remapped to 0.928571 in deferred
RT2.y high7 = mask/fade packed value
RT2.z high7 = normal-light scalar
```

If no metadata exists, the producer/consumer chain becomes the primary naming source together with image evidence.

### 6. Export Texture, RT, And Channel Evidence

Prefer actual RenderDoc exports in reports:

- input textures: base color, normal map, alpha or mask
- output RTs: main output first, then other RTs only when they matter
- alpha as a separate single-channel view, especially `R10G10B10A2_UNORM` 2-bit alpha
- key channel single-channel views when semantics are in dispute

DX11 exported images may be vertically flipped. Use flipped versions for report display when needed, but keep original exports.

Do not over-enhance, crop away context, or replace buffer evidence with flowcharts. The reader needs to see real buffer values and structure.

### 7. No-metadata Semantic Recovery Order

When metadata is missing or insufficient, restore semantics in this order:

1. Inspect the current RT or texture image and note what the channel visually behaves like.
2. Inspect how the downstream shader reads that channel.
3. Inspect how the producer shader writes that channel.
4. If still unclear, export a shader-edit probe that writes the disputed pre-quantized or branch-driving intermediate value directly to an RT.
5. If still unclear, keep a neutral name and add a human-review item instead of forcing semantics.

Use evidence-level tags in notes or reports:

- `producer-confirmed`
- `consumer-only`
- `probe-supported`
- `ambiguous`

## Naming Rules

### Confirmed Material Properties

Use original metadata property names when confirmed:

```hlsl
float _NormalScale = CB2_m0[1u].x;
float _SubsurfaceIntensity = CB2_m0[2u].y;
float _Transmission = CB2_m0[2u].z;
float _MaskOnDiffuse = CB2_m0[3u].z;
float _MaskOnTransmission = CB2_m0[3u].w;
```

### Vector Names

Merge scalars that clearly belong together:

```hlsl
float2 normalMapVector = normalMapSample.xy;
float2 tangentNormal = ...;
float3 worldNormal = ...;
float2 octNormal = ...;
```

Avoid:

```hlsl
float normalMapX;
float normalMapY;
float octNormalXY;
```

Do not keep suffixes like `XY` when the type already states the component count. Use `octNormal`, not `octNormalXY`.

### Unconfirmed Semantics

Use neutral structured names:

```hlsl
uint packedMaskFadeHigh7;
float localPositionFade;
float terrainFadeInverse;
float unknownScalarA;
```

Do not prematurely name values as:

```hlsl
specularMask
f0Selector
ao
transmissionFinal
```

Use final BRDF or material terms only after downstream shader evidence closes the loop.

### Packed Bit Names

Packed names must include bit width and source:

```hlsl
uint packedSubsurface5Bits;
uint packedTransmissionHigh7;
uint packedMaskFadeHigh7;
```

The report must state the channel and bit range:

```text
RT2.x high7
RT2.x low3
RT2.w low2
```

Avoid opaque names such as `payload`.

### Fade And Mask Names

Confirm input space before naming fade or mask terms.

Example:

```hlsl
// VS
TEXCOORD_6 = POSITION.xyz;

// PS
float3 outputLocalPositionFadeVector = TEXCOORD_6 + float3(0.0f, CB2_m0[9u].w, 0.0f);
SV_Target_4.w = f(length(outputLocalPositionFadeVector), CB2_m0[9u]);
```

Do not call this `camera distance fade`. A more accurate name is:

```text
local-vertex-position fade mask
```

For upright grass cards or blades, this may visually look like a root-to-tip or bottom-to-top gradient.

## Probe Policy

Use shader-edit probes only for key unresolved outputs or branches. They are evidence helpers, not a replacement for code, binding, and flow analysis.

Default probe policy:

- limit to 1-3 probes per disputed output
- probe the packed pre-quantized value or branch-driving intermediate first
- keep edits minimal and close to the decompiler output
- save baseline and edited artifacts
- always call `revert_shader_edit` before finishing

Good probe outputs:

- pack-before values written directly to `SV_Target.rgb`
- one branch mask written to grayscale
- one disputed scalar written to a single channel

## Human Review Queue

If semantics remain unresolved, do not silently stop and do not hard-name them.

Create `review/needs_human_review.md` and include for each item:

- stable item id, for example `H1`
- artifact path
- current hypothesis
- why current evidence is insufficient
- suggested next probe if any

The main report should include a short `Human Review` section that points to this file.

## Validation Checklist

Do at least these checks after restoration:

1. Compile the annotated HLSL when the target/profile and local toolchain are available:

```powershell
& 'C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\fxc.exe' /T ps_5_0 /E main /nologo /Fo NUL .\Foliage\hlsl\eid_13525_ps_annotated.hlsl
```

2. Search for misleading leftover names:

```powershell
rg -n "spec/F0|payload|distance/fade|packedScalar|_\\d+" Foliage\hlsl Foliage\Report
```

3. Compare against the original decompiled file:

- bitfield insert/extract widths are unchanged
- `round`, `clamp`, `mad`, and `uint` conversions are unchanged
- `R10G10B10A2_UNORM` 10-bit/2-bit scale constants are correct

4. Compare against downstream consumers:

- the render target is actually read by that pass
- channel or bit unpacking matches the producer layout
- if the consumer only remaps an intermediate value, do not name it as final BRDF semantics

5. Compare against exported images:

- RGB roughly matches the proposed semantics
- alpha is checked as its own channel
- if visuals conflict with the name, trace input space again instead of forcing the interpretation

6. Confirm probe hygiene:

- baseline artifact saved
- edited artifact saved
- replacement reverted

## Report Shape

Use the shader-restoration report structure from `report-format.md` for `reverse-action`.

For each code block include:

- HLSL line range or snippet
- input source
- output target
- confirmed semantics
- evidence level
- unresolved parts

Do not write a report that has only flowcharts or resource lists and no code evidence.

## Common Pitfalls

- treating metadata defaults as runtime values
- naming `length()` as camera distance without proving the input space
- naming a deferred-lighting intermediate as a final BRDF term
- mixing RT alpha with an input texture alpha
- ignoring `R10G10B10A2_UNORM` bit packing
- rewriting expressions for readability and changing bit-level behavior
- stopping at `consumer-only` when one producer hop or one probe would resolve the ambiguity

## Grass HGBuffer Confirmed Findings

Keep these as example findings, not global rules for every shader:

- `_NormalMap.xy` is tangent normal source
- `_NormalMap.z` is roughness source
- `_NormalMap.w` is MaskA and participates in RT2 packed scalar; it is not RT4 alpha
- `RT2.x low3 + RT2.w low2` stores the 5-bit `_SubsurfaceIntensity` value
- `RT2.x high7` stores a `_Transmission`-related packed value
- `RT2.y low3` is constant `4`, remapped to `0.928571` in deferred; final BRDF semantics remain unnamed
- `RT2.y high7` is mask/fade packed value
- `RT2.z high7` is normal-light scalar
- `RT3.xy` is oct normal, `RT3.z` is roughness, and current grass variant writes `RT3.w = 0`
- `RT4.rgb` is base color/tint, `RT4.a` is local-vertex-position fade mask
