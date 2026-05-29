---
name: renderdoc-analysis
description: Analyze RenderDoc evidence from renderdoc-mcp. Use for action reverse engineering, pass classification, resource-flow tracing, shader/material usage, frame reports, pipeline reconstruction, and controlled shader edit experiments.
---

# RenderDoc Analysis

Use this skill only after collecting facts from `renderdoc-mcp`.
Working boundary:
- MCP is primarily the observe layer.
- This skill is the analysis layer.
- Shader edit tools are controlled replay experiments for testing a specific hypothesis; do not use them as a substitute for shader, binding, IO, and resource-flow evidence.
- Name packet fields or inspect outputs when you cite evidence.
- Treat script outputs as evidence helpers, not final authority.
- If evidence is insufficient, stop at a broader family.
- If multiple qrenderdoc windows may be open, call `list_live_windows` first and pass `window_id` to every live MCP tool. For bundled scripts, set `RENDERDOC_MCP_WINDOW_ID`.
- When you finish using a qrenderdoc window or capture for the current task, close that opened content/window instead of leaving extra RenderDoc windows around.
- If a qrenderdoc window was already open before installing or updating the bridge extension, restart it; extension methods are not hot-reloaded.

Task routes: `analyze-pass`, `trace-resource-flow`, `analyze-material-usage`, `reverse-action`, `shader-edit-experiment`, `build-frame-report`, `reverse-render-pipeline`

Route note:
- `analyze-pass`, `trace-resource-flow`, and `build-frame-report` stay lightweight.
- `reverse-action` is the strict high-quality shader-restoration path. Do not fall back to a resource-inventory-only report just because metadata is missing.

Read only the references you need:
- routing: `references/tool-map.md`
- workflow: `references/workflows.md`
- taxonomy: `references/pass-taxonomy.md`, `references/render-pass-taxonomy.md`
- category checks: `references/pass-checklists.md`
- conclusion rules: `references/conclusion-rules.md`
- evidence guardrails: `references/evidence-guardrails.md`
- report format: `references/report-format.md`
- shader motifs: `references/shader-patterns.md`
- shader restoration and naming: `references/shader-restoration-workflow.md`
- shader decompiler install/use: `references/decompiler.md`
- shader edit experiments: `references/workflows.md`, `references/tool-map.md`, `references/decompiler.md`

Script rule:
- Always read `*_summary.json` first.
- Read `*_full.json` only when summary confidence is `low` or `needs_detail` is non-empty.
- Do not dump a whole full JSON into context when a few fields are enough.

Useful scripts:
- `scripts/build_pass_evidence_bundle.py`
- `scripts/scan_pass_visuals.py`
- `scripts/classify_pass_taxonomy.py`
- `scripts/analyze_pass.py`
- `scripts/build_shader_restoration_report.py`

## analyze-pass

Use for pass role, pass family, RT meaning, or semantic naming.

Decision tree:

1. `get_pass_packet` is the required entry.
2. If the pass is only clear/copy/resolve, conclude and stop.
3. Use `data.rep_draw` first. It already includes `pipe` and `shader`.
4. Only call `get_draw_packet`, `inspect_pipeline_state`, or `inspect_shader` when you need a non-representative event.
5. Cluster the pass before naming it. Let the dominant cluster decide the family.
6. Default to one `inspect_texture_usage` on RT slot 0.
7. Only inspect a second RT when the pass is multi-RT and RT semantics matter. Hard cap: 2 RTs.
8. Export overlay or prev/current RT only when screen contribution is genuinely unclear.
9. For multi-RT or GBuffer-like passes, inspect only the first key downstream consumer that is needed to keep RT semantics honest.
10. Before writing the answer, read `references/report-format.md`.

## trace-resource-flow

Use for producer, first consumer, and downstream chain questions.

Default path:

1. `inspect_texture_usage`
2. `get_pass_packet` only for the producer or first key consumer
3. `get_draw_packet` only if one specific event matters
4. Write the result with `references/report-format.md`

## analyze-material-usage

Use for shader bindings, sampled textures, and likely material role.

Default path:

1. `get_draw_packet`
2. use packet shader data first
3. call `inspect_shader` only if packet shader data is not enough
4. `inspect_texture_usage` only for the few bindings that matter
5. `inspect_mesh` only if geometry context changes the answer
6. Write the result with `references/report-format.md`

## reverse-action

Use for one draw or dispatch when the goal is to restore shader behavior at high quality: readable HLSL, naming evidence, packed-output semantics, image evidence, and explicit unresolved items.

Default path:

1. `get_draw_packet` is the required entry.
2. Use draw-packet `context` first for marker path, parent pass, root pass, position, and neighbors. Add `get_pass_packet` only when broader pass role or sibling evidence beyond packet context matters.
3. For draws, `inspect_mesh` is the default, not optional. You need vertex attributes plus vertex/index buffer bindings before explaining the shader. For dispatches, mark geometry as not applicable.
4. For draws, inspect both `vs` and `ps` unless one stage is proven irrelevant. For dispatches, inspect `cs`.
5. Create or reuse the action working directory before code reading. If the user supplied a directory, use it. Otherwise use the current report/bundle directory for that action, or `.state/action_reverse/<capture-or-session>/eid_<eid>/`. Ensure the working directory also contains `assets/`, `debug_shaders/`, and `review/`.
6. Decompile the inspected action shader stages with Ruri to HLSL and export them into the action working directory before writing the reverse report. For draws, decompile `vs` and `ps` unless one stage is proven irrelevant; for dispatches, decompile `cs`. Name files predictably, for example `eid_<eid>_<stage>_<shader-name-or-sid>.hlsl`. Keep the exported HLSL as the primary artifact. If Ruri is unavailable or decompilation fails, record the reason and continue with `get_shader_disasm`; do not skip this silently.
7. Read `references/shader-restoration-workflow.md` before renaming variables, assigning RT/channel semantics, or writing the final report. In `reverse-action`, this is not optional.
8. Build a binding inventory before drawing conclusions:
   - `inspect_shader.bind`
   - `inspect_shader.bindings`
   - `inspect_shader.cbufs`
   - `inspect_shader.debug`
   - `inspect_shader.sig`
   - draw-packet `io`
   - mesh `vb/ib` data for draw events
9. Annotate the exported HLSL, or an adjacent `<shader>.notes.md`, before finalizing. Preserve the decompiled code structure and identifiers. Do not rewrite it into a new pseudocode shader, do not construct helper functions, and do not invent variable/function names unless accurate metadata or direct shader definitions provide those names. Treat metadata names as candidates until runtime cbuffer values, binding evidence, code use, and producer/consumer flow support the rename. Use original decompiler names, resource slots, RIDs, or short comments when semantics are not confirmed. If metadata or shader definitions provide a real symbol name and the evidence chain supports it, keep that spelling instead of shortening it, for example `_MultiscatteringLUT` or `_IrradianceVolumeClipmapTextureALod0`. For inferred consumer-side locals, use complete semantic names such as `roughness`, `normal`, `worldPos`, `viewDir`, and `heightFogNoiseBlend`; avoid terse abbreviations such as `rough`, `n`, or `ws` unless they are part of a real source symbol. Prefer `float3`/`float4` vector locals for vector quantities and split into `.x/.y/.z` components only where scalar code requires it. Keep evidence and confidence in comments or notes. The annotation must split code by large functional blocks only; avoid dense line-by-line comments. Add concise comments for:
   - declaration / resource setup
   - vertex/input reconstruction or coordinate prep
   - texture loads, sampling, decode, and masks
   - material, lighting, composite, or compute evaluation
   - output packing / final RT or UAV writes
10. For packed RT/UAV outputs, preserve exact bit operations and numeric conversions (`round`, `clamp`, `mad`, `uint`, bitfield insert/extract). Name packed values with channel, source, and bit width where known, and report layouts as channel/bit ranges such as `RT2.x high7`, `RT2.x low3`, or `RT2.w low2`.
11. Annotate input resources near their HLSL declarations or in a dedicated resource note. For each important `t#`, `s#`, `cb#`, `u#`, and `vb/ib`, include slot, resource name/RID when available, format/dimensions when available, actual code role, and semantic status (`consumer-only`, `producer-confirmed`, or `ambiguous`).
12. Use `get_shader_code` first for the decisive stage. It should return source when available and disassembly otherwise.
13. Use `get_shader_source` or `get_shader_disasm` directly only when you need explicit control over the fallback path, file selection, or disassembly cross-check.
14. Segment the decisive code by line ranges. At minimum identify:
   - declaration / resource setup
   - input reconstruction or coordinate prep
   - texture sampling and decode blocks
   - lighting or material evaluation blocks
   - output packing / final writes
15. Use HLSL block comments and disassembly line ranges explicitly. Report findings as ranges such as `lines 1-40`, `41-96`, not just free-form summaries. If decompiled code has only generated identifiers, refer to original generated names or slots rather than renaming them. If HLSL and disassembly disagree, trust binding/IO facts and disassembly first, and state the mismatch.
16. Treat resource semantics as unproven until tied to actual code use. Resource name, format, dimensions, producer evidence, and downstream use all matter.
17. Trace producer evidence for semantic key inputs before assigning a narrow meaning. Key inputs include resources or channels used for branches, masks, alpha/transmittance, depth reconstruction, GBuffer decode, lighting lookup, or final output modulation. Default to at most 3 key inputs and one producer hop unless the user explicitly asks for deeper tracing.
   - Start with `inspect_texture_usage` for the resource and use `producer`, `last_write`, `first_read_ctx`, and `first_ps_read_ctx` as evidence.
   - If producer identity or channel meaning changes the conclusion, inspect the producer draw/dispatch and the relevant shader stage.
   - For producer shaders, identify which RT/UAV channel is written and what broad input family feeds it, without inventing specific semantic names from the consumer alone.
   - Classify resource meanings as `consumer-only`, `producer-confirmed`, or `ambiguous`. Use broader names when producer evidence is missing or mixed.
18. Treat metadata as optional acceleration, not as a gate. If metadata is missing, keep the same restoration workflow and recover semantics in this order:
   - current RT/texture image evidence
   - downstream read behavior
   - producer write behavior
   - controlled shader-edit probes
   - unresolved item queued for human review
19. Use `inspect_texture_usage` for the few inputs or outputs that change the conclusion. Default priority:
   - one main output RT or UAV
   - one disputed or branch-driving input texture
   - one downstream consumer if output channel meaning is uncertain
20. Export image evidence for key inputs and outputs. At minimum include the main output RT; add alpha single-channel views, key channel single-channel views, and flipped DX11 display copies when they materially improve interpretation.
21. For each key unresolved output meaning, allow 1-3 minimal shader-edit probes. Probe the packed pre-quantized value or branch-driving intermediate first, save baseline and edited artifacts, and always call `revert_shader_edit` before finishing.
22. Compile the annotated HLSL when the original entry/profile and local toolchain are available. Record pass/fail in the report; do not silently skip failed compilation.
23. Put any still-unresolved semantics into `review/needs_human_review.md` with linked images, hypothesis text, and the current evidence level.
24. Write the result with `references/report-format.md` and use `references/shader-patterns.md` for motif recognition. In `reverse-action`, prefer the shader-restoration report shape over the lighter generic action report.

Reverse-action acceptance bar:
- export inspected shader stages to HLSL in the action working directory, or state why this failed
- split and comment the exported HLSL by large functional blocks before reporting
- keep the exported HLSL close to the decompiler result; do not replace it with a handcrafted pseudocode shader or self-built helper functions
- do not invent semantic variable/function names without accurate metadata or direct definitions; use generated names, slots, RIDs, or comments
- list the key `t#`, `u#`, `cb#`, and `vb/ib` inputs
- annotate important input resources with slot, RID/name, format/dimensions when available, actual code role, and confidence status
- explain what each important resource is doing, not just that it is bound
- for key mask/GBuffer/depth/lighting inputs, state whether the meaning is consumer-only, producer-confirmed, or ambiguous
- split the decisive shader into line ranges with a function for each range
- describe `o#` or UAV outputs with channel-level evidence when available
- keep pass-family guesses secondary to shader/resource facts
- do not use `BLENDWEIGHTS/BLENDINDICES` as semantic proof beyond mesh-format context
- for shader restoration, keep the raw decompiled HLSL plus annotated artifact or notes; each semantic rename must cite the supporting metadata/runtime/code/producer-consumer evidence or remain low-level
- for packed GBuffer/HGBuffer outputs, report channel-level and bit-level layouts instead of broad names such as `payload`
- when metadata is missing, do not downgrade to a broad inventory report; use image evidence, downstream/producer flow, and shader-edit probes to push semantics as far as they will go
- include image artifacts for key inputs/outputs and single-channel views where they affect the conclusion
- include compile validation when the toolchain is available
- include `review/needs_human_review.md` when any semantics remain unresolved

## shader-edit-experiment

Use only when the user asks to test a shader modification, or when a specific shader/output hypothesis remains disputed after normal observation.

Default path:

1. Select the live target with `list_live_windows` when needed, and pass `window_id` to every live tool call.
2. Inspect the target action first with `get_draw_packet` and `inspect_shader`; identify `eid`, `stage`, current shader RID, entry point, likely compile profile, and output RT/UAV.
3. Export or reuse the decompiled HLSL in the action working directory. Keep edits minimal and close to the Ruri output.
4. Save a baseline output image with `save_event_output_texture` before applying any edit.
5. Call `get_target_shader_encodings` and require `HLSL` support before compiling HLSL.
6. Apply the edit with `apply_shader_edit(eid, stage, source_path|source, source_encoding="hlsl", entry, profile)`. Use the same entry/profile observed from the shader, for example `main` and `ps_5_0` for many D3D11 pixel shaders.
7. Save the edited output image, then compare it with the baseline visually or by hash/pixel statistics.
8. Always call `revert_shader_edit(eid, stage)` before finishing the experiment. If multiple edits are applied to the same shader, the latest MCP-created replacement is the one reverted.
9. Report the baseline artifact, edited artifact, exact HLSL file or edit, replacement result, and whether the image difference supports the hypothesis.

Shader edit guardrails:
- Do not leave a replay replacement active after the task.
- Do not infer semantic meaning from a diagnostic color alone; tie it back to code ranges, bindings, IO, and resource flow.
- Prefer simple output probes such as writing one intermediate value to `SV_Target` over broad rewrites.
- If `apply_shader_edit` is unavailable in an existing qrenderdoc window, restart qrenderdoc after reinstalling the extension.

## build-frame-report

Use for a concise frame summary.

Default path:

1. `get_frame_packet`
2. `get_pass_packet` for only the passes you discuss
3. add targeted `inspect_*` calls only where they change the conclusion
4. Write the result with `references/report-format.md`

## reverse-render-pipeline

Use for high-level frame reconstruction.

Default path:

1. `list_passes`
2. `get_frame_packet`
3. targeted `get_pass_packet` on key passes
4. add `inspect_*` only on disputed stages
5. Write the result with `references/report-format.md`

Final rules:
- Prefer broad families over shaky narrow labels.
- Do not let one representative draw define the whole pass.
- Do not translate `fullscreen`, `local`, `simple mesh`, or `skeletal mesh` directly into semantics.
- For disputed passes, force `top1 / top2 / support / counter-evidence / decision / final name`.
