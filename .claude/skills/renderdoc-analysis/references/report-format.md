# Report Format

Write concise reports that separate facts from interpretation.

## Pass report

```text
Pass: <name> (eid=<eid>)

dominant cluster:
- <cluster>

mixed-in items:
- <secondary item>

Candidates:
- top1: <family / label>
- top2: <family / label or none>

Support for top1:
- <fact>

Support for top2:
- <fact>

Counter-evidence:
- <fact>

Decision:
<why top1 beats top2>

Final Name:
<family / label or broad family>

Uncertainties:
- <gap>
```

## Resource-flow report

```text
Resource: <rid> <name>
Producer: <producer>
First consumer: <consumer>

Flow:
- <edge>

Notes:
- <gap or limit>
```

## Frame report

```text
Frame Overview
- API: <api>
- Path: <path>
- Pass count: <count>

Key Passes
- <pass>: <why it matters>

Resource Flow Notes
- <note>

Next Checks
- <check>
```

## Shader restoration report

Use this structure for strict `reverse-action` restoration work:

```text
Action: <eid> <name> (<Draw|Dispatch>)
Capture: <path or unknown>
Marker Path: <marker path or unknown>
Parent Pass: <nearest marker pass name or unknown>
Root Pass: <outermost pass name or unknown>
Position: <index within pass or unknown>
Neighbors:
- prev: <eid or none>
- next: <eid or none>

Artifacts:
- raw HLSL: <path>
- annotated HLSL or notes: <path>
- report dir: <path>

Geometry:
- <topology / counts / attribute pattern, or not applicable>
- <vertex/index buffer bindings, or not applicable>

Bindings:
- <important t#/s#/cb#/u#/vb/ib input>

Metadata Candidates:
- <property candidate and why it is only a candidate>

Runtime CBuffer Checks:
- <cb slot / symbol / runtime value / candidate / status>

Code Blocks:
- <stage lines A-B: what this range does>
- <stage lines C-D: what this range does>

Outputs:
- <rt/uav target and broad role>
- <for packed outputs: channel/bit layout, pre-quantized meaning, and evidence level>

Producer / Consumer Chain:
- <producer write or consumer read fact>

Image Evidence:
- <key input/output image and why it matters>
- <alpha or single-channel image and why it matters>

Probe Evidence:
- <probe id / hypothesis / artifact / result>

Conclusion:
- <restored semantic understanding>
- <what remains low-confidence>

Human Review:
- <review item id / image / current hypothesis>

Validation:
- <compile result>
- <other checks>
```

Acceptance:

- use this shape for `reverse-action`, even when metadata is missing
- include raw plus annotated HLSL artifacts
- include runtime cbuffer checks when candidate names are promoted
- include channel-level and bit-level layouts for packed outputs
- include image evidence for key inputs/outputs and single-channel views where relevant
- record shader-edit probes as experiment artifacts, not as standalone proof
- unresolved semantics must appear in a human-review section instead of being hard-named

## Action reverse report

```text
Action: <eid> <name> (<Draw|Dispatch>)
Marker Path: <marker path or unknown>
Parent Pass: <nearest marker pass name or unknown>
Root Pass: <outermost pass name or unknown>
Position: <index within pass or unknown>
Neighbors:
- prev: <eid or none>
- next: <eid or none>

Geometry:
- <topology / index count / instance count / attribute pattern>
- <vertex buffers and index buffer summary, or not applicable>

Fixed-function State:
- <blend / depth / rasterizer facts, or not applicable / API-limited>

Shader Artifacts:
- <HLSL path for each inspected stage, or decompile failure reason>

Resource Inventory:
- VS: <t#/cb#/vb inputs and roles>
- PS: <t#/cb#/s# inputs and roles>
- CS: <t#/u#/cb# inputs and roles, or not applicable>

Input Resource Notes:
- <slot/rid/name/format/dimensions/code role/status for important inputs>

Constant Buffers:
- <cb slot name size variables and likely usage>

Shader Segments:
- <HLSL block or disasm lines A-B: what this range does>
- <HLSL block or disasm lines C-D: what this range does>

Outputs:
- <o#/rt/uav target and likely channel meaning>
- <for packed outputs: channel/bit layout, scale constants, and producer/consumer evidence>

Shader Behavior:
- <stage and entry>
- <how resources are actually used in code>

Screen Contribution:
- <overlay or before/after observation, if collected>

Downstream:
- <first visible consumers of the main outputs>

Conclusion:
- <what this action is doing>
- <why that conclusion fits the evidence>

Limits:
- <missing stage, partial binding map, IO truncation, API limitation, or uncertainty>
```

## Acceptance

- cite the pass name and stats when available
- cite at least one packet or inspect field
- keep evidence factual
- keep interpretation separate
- do not end with only geometric labels such as `fullscreen`, `local`, or `mixed`
- if RT or channel semantics are not backed by downstream use, keep them provisional
- for action reverse reports, include context, resources, and shader behavior
- for action reverse reports, cite exported HLSL paths or state why decompilation failed
- for action reverse reports, include annotated input-resource roles for important `t#`, `s#`, `cb#`, `u#`, and `vb/ib` inputs
- for dispatch events, mark geometry or fixed-function sections as not applicable instead of forcing graphics wording
- when the draw-packet IO list is partial, say so explicitly instead of implying a complete binding map
- do not translate full disassembly line by line; summarize only the motifs that matter to the conclusion
- action reverse reports must explain the important resources, not just list them
- action reverse reports must use explicit code line ranges for the decisive stage
- do not use `BLENDWEIGHTS/BLENDINDICES` as semantic proof beyond mesh-format context
- when restoring shader names, distinguish metadata candidates from runtime-proven cbuffers or producer/consumer-proven channel semantics
- packed GBuffer/HGBuffer reports must include channel-level and bit-level layouts when those bits drive the conclusion
- use the `Shader restoration report` shape instead of this lighter template when `reverse-action` is doing full shader restoration
