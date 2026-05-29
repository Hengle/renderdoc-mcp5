# Workflows

## Summary First

- Read `*_summary.json` first.
- Read `*_full.json` only when summary confidence is `low` or `needs_detail` is non-empty.
- If you need full output, read only the relevant fields or sections instead of the whole file.

## Live Window Selection

1. Use `list_live_windows` when more than one qrenderdoc window may be active.
2. Match the intended capture by `capture_path`.
3. Pass `window_id` on all live MCP calls for that task.
4. For bundled scripts, set `RENDERDOC_MCP_WINDOW_ID` before running the script.
5. Treat a multiple-window error as a target-selection problem, not as evidence failure.
6. Restart qrenderdoc after bridge extension install/update; existing windows do not hot-load new Python methods.

## Pass Analysis

1. Start with `get_pass_packet`.
2. Use `data.rep_draw` first; it already carries pipeline and shader summary.
3. Cluster the pass before naming it.
4. If the dominant cluster is still unclear, inspect 1-2 more representative events with `get_draw_packet`.
5. Call `inspect_pipeline_state` or `inspect_shader` only for non-representative events that matter.
6. Default to one `inspect_texture_usage` on RT slot 0.
7. Add a second RT only when the pass is multi-RT and RT semantics matter. Stop at 2 RTs.
8. Use overlay or prev/current RT comparison only when screen contribution is disputed.
9. For multi-RT or GBuffer-like passes, inspect only the first key downstream consumer needed for RT semantics.
10. Write the answer with `report-format.md`.

## Resource Flow

1. Start with `inspect_texture_usage`.
2. Add `get_pass_packet` only for the producer or first key consumer.
3. Add `get_draw_packet` only when one event matters more than the pass packet.
4. Write the answer with `report-format.md`.

## Material Or Shader Usage

1. Start with `get_draw_packet`.
2. Use packet shader data first.
3. Call `inspect_shader` only when packet shader data is insufficient.
4. Limit `inspect_texture_usage` to the few bindings that matter.
5. Add `inspect_mesh` only when geometry context changes the answer.
6. Write the answer with `report-format.md`.

## Action Reverse Engineering

This is the strict high-quality shader-restoration workflow. Do not treat it as a lightweight inventory report.

1. Start with `get_draw_packet`.
2. Use draw-packet `context` first for marker path, parent pass, root pass, ordering, and neighbors. Add `get_pass_packet` only when broader pass role or sibling evidence beyond packet context matters.
3. If the event is a draw, `inspect_mesh` is the default because vertex attributes plus `vb/ib` bindings are part of the reverse-engineering evidence. If the event is a dispatch, mark geometry as not applicable.
4. For draws, inspect both `vs` and `ps` unless one stage is clearly irrelevant. For dispatches, inspect `cs`.
5. Treat fixed-function state as API-limited when `state.limited_to_source_api` is true.
6. Create or reuse the action working directory before shader code reading. Use the user-provided directory when present; otherwise use the current report/bundle directory or `.state/action_reverse/<capture-or-session>/eid_<eid>/`. Ensure `assets/`, `debug_shaders/`, and `review/` exist under that directory.
7. Decompile the inspected shader stages with Ruri to HLSL and export them into that working directory. For draws, export `vs` and `ps` unless a stage is proven irrelevant; for dispatches, export `cs`. If decompilation fails, record the failure and continue from RenderDoc disassembly.
8. Read `shader-restoration-workflow.md` before renaming variables or assigning RT/channel semantics. In `reverse-action`, this is mandatory.
9. Build a binding inventory from `inspect_shader.bind`, `inspect_shader.bindings`, `inspect_shader.cbufs`, `inspect_shader.sig`, draw-packet `io`, and mesh `vb/ib` data before writing semantics.
10. Annotate the exported HLSL, or an adjacent notes file, by large functional blocks: declarations, input reconstruction, texture decode, material/lighting/composite or compute evaluation, and output packing/writes. Preserve decompiled behavior and keep uncertain names low-level.
11. Promote metadata names to material or cbuffer names only when runtime cbuffer values, binding evidence, code use, and producer/consumer flow support the rename.
12. For packed RT/UAV outputs, preserve exact bit operations and report channel/bit layouts such as `RT2.x high7`, `RT2.x low3`, and `RT2.w low2`.
13. Annotate important input resources with slot, RID/name, format/dimensions when available, actual code role, and semantic status (`consumer-only`, `producer-confirmed`, or `ambiguous`).
14. Add `get_shader_disasm` for the decisive stage and use it to cross-check HLSL and cite code ranges.
15. Use explicit HLSL block names and disassembly line ranges in the report, not just motif names.
16. Treat metadata as optional acceleration. Without metadata, keep the same workflow and recover semantics from image evidence first, then downstream reads, then producer writes, then controlled probes, and finally human-review queue items.
17. Use `inspect_texture_usage` for only the few outputs or disputed inputs that materially change the conclusion. Default priority is one main output plus one disputed input and one downstream consumer if needed.
18. Use `io.in_tex_meta`, `io.out_rt_meta`, `io.out_uav_meta`, and `io.out_next_meta` to judge truncation or partial downstream coverage. Do not treat `inspect_shader.bind.srv` and `io.in_tex` as directly comparable counts.
19. Export image evidence for key inputs and outputs. Include alpha single-channel views and flipped DX11 display copies when they materially improve interpretation.
20. For each key unresolved output meaning, allow 1-3 minimal shader-edit probes. Probe pre-quantized packed values or branch-driving intermediates first. Save baseline and edited artifacts, then revert the replacement.
21. Compile the annotated HLSL when the original entry/profile and local toolchain are available. Record pass/fail in the report.
22. Put still-unresolved semantics into `review/needs_human_review.md` with linked images, hypotheses, and current evidence levels.
23. Write the answer with `report-format.md` and consult `shader-patterns.md` for motif recognition. Use the shader-restoration report shape for `reverse-action`.

## Shader Edit Experiment

Use this workflow only to test a specific shader/output hypothesis.

1. Select the live qrenderdoc window with `list_live_windows` when needed.
2. Identify the target action and stage with `get_draw_packet` and `inspect_shader`.
3. Record the current shader RID, entry point, compile profile, relevant output RT/UAV, and the exact HLSL artifact being edited.
4. Save the baseline output with `save_event_output_texture`.
5. Call `get_target_shader_encodings`; for Ruri output, require `HLSL`.
6. Make the smallest useful HLSL edit. Prefer writing one intermediate value or diagnostic color to `SV_Target`/the relevant output over rewriting the shader.
7. Call `apply_shader_edit` with `eid`, `stage`, `source_path` or `source`, `source_encoding="hlsl"`, `entry`, and `profile`.
8. If compilation fails, report the compiler errors and stop without claiming visual evidence.
9. If compilation succeeds, save the edited output with `save_event_output_texture` and compare it with the baseline by visual inspection, hash, or pixel statistics.
10. Call `revert_shader_edit(eid, stage)` before finishing.
11. Report the exact edit, baseline artifact, edited artifact, replacement result, comparison result, and any remaining uncertainty.

Guardrails:

- Treat shader edit results as experimental evidence that supports or rejects one hypothesis.
- Keep normal shader analysis, bindings, IO, and resource-flow evidence as the basis for semantic claims.
- Do not leave the replacement active in the replay session.
- If repeated edits target the same shader, revert at the end; the bridge tracks the latest MCP-created replacement.

## Frame Report

1. Start with `get_frame_packet`.
2. Pull `get_pass_packet` only for passes discussed in the report.
3. Add targeted `inspect_*` calls only where they change the conclusion.
4. Keep the report shorter than the packet material it summarizes.
