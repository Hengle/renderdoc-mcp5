# Tool Map

Use this file to choose the minimum tool set for each analysis task.

## Live Target Setup

When a task uses live qrenderdoc data:

- call `list_live_windows` first if more than one qrenderdoc window may be open
- pick the `window_id` whose `capture_path` matches the target capture
- pass that `window_id` to every live MCP tool call
- for bundled scripts, set `RENDERDOC_MCP_WINDOW_ID=<window_id>`
- if qrenderdoc was already open before bridge extension install/update, restart it; Python extension methods are not hot-reloaded

## Shader Edit Tools

Use these only for controlled replay experiments after the target shader/output is already identified:

- `get_target_shader_encodings`: check whether the live replay supports compiling `HLSL`, `DXBC`, or other target encodings.
- `apply_shader_edit`: compile edited source or bytecode and replace the current shader resource for a target `eid` and `stage`.
- `revert_shader_edit`: remove the MCP-managed replacement and free the temporary target shader resource.

Good stopping point:

- a baseline output artifact was saved before the edit
- the edited output artifact was saved after the edit
- the replacement was reverted before finishing
- the image difference is tied back to shader code, bindings, IO, or resource-flow evidence

## `analyze-pass`

Start with:

- `list_passes`
- `get_pass_packet`

Add when needed:

- `get_draw_packet` for a representative event
- `inspect_pipeline_state`
- `inspect_shader`
- `inspect_texture_usage` for important outputs

Good stopping point:

- you can name the pass
- you can cite its dominant event type
- you can cite its output pattern or shader stage pattern

## `trace-resource-flow`

Start with:

- `inspect_texture_usage`

Add when needed:

- `get_pass_packet` for producer or consumer context
- `get_draw_packet` when a single event matters more than the pass summary

Good stopping point:

- you can identify producer and first consumer
- you can distinguish downstream major consumers from incidental reads

## `analyze-material-usage`

Start with:

- `get_draw_packet`

Add when needed:

- `inspect_shader` for another stage or fuller binding detail
- `inspect_texture_usage`
- `inspect_mesh`

Good stopping point:

- you can name the dominant stage and entry point
- you can cite the important binding counts or key sampled resources

## `reverse-action`

Start with:

- `get_draw_packet`
- `inspect_mesh` for draw events
- `inspect_shader` for `vs + ps` on draw events, or `cs` on dispatch events

Add when needed:

- `get_pass_packet` for broader pass role or sibling evidence beyond draw-packet context
- Ruri HLSL export for the inspected action shader stages into the action working directory
- `get_shader_disasm` for motif recognition in the decisive stage
- `inspect_texture_usage` for the few outputs or disputed inputs that matter downstream
- `read_buffer` when metadata candidates need runtime cbuffer confirmation
- `apply_shader_edit` / `revert_shader_edit` for 1-3 controlled probes on key unresolved outputs
- exported RT or texture images, including alpha single-channel views, for semantic confirmation

Good stopping point:

- exported or explicitly failed HLSL artifacts are recorded for the inspected shader stages
- annotated HLSL or notes exist beside the raw decompile
- you can list the important `t#`, `u#`, `cb#`, and `vb/ib` inputs
- you can annotate what important input resources do in code
- you can explain the main shader code ranges and what each range does
- you can describe `o#` or UAV outputs with evidence tied to code or downstream consumers
- packed outputs are described at channel/bit level, not as broad payloads
- if metadata exists, runtime cbuffer values and metadata candidates are aligned before renaming
- if metadata does not exist, image evidence plus downstream/producer flow and controlled probes push semantics as far as they can go
- unresolved items are queued in `review/needs_human_review.md` instead of being hard-named
- you can separate hard evidence from inferred material or effect role

## `shader-edit-experiment`

Start with:

- `get_draw_packet`
- `inspect_shader` for the target stage
- `save_event_output_texture` for the baseline output
- `get_target_shader_encodings`

Add for the experiment:

- Ruri HLSL export or an existing HLSL file close to the inspected shader
- `apply_shader_edit` with `eid`, `stage`, `source_path` or `source`, `source_encoding="hlsl"`, and the observed `entry`/`profile`
- `save_event_output_texture` for the edited output
- `revert_shader_edit` before finalizing

Good stopping point:

- compile succeeded or the compile errors are reported
- baseline and edited artifacts are named
- the shader replacement is reverted
- the conclusion is framed as experimental evidence, not standalone semantic proof

## `build-frame-report`

Start with:

- `get_frame_packet`

Add when needed:

- `get_pass_packet` for important passes
- `inspect_pipeline_state`
- `inspect_shader`
- `inspect_texture_usage`

Good stopping point:

- you can identify the frame backbone
- you can justify why each discussed pass matters

## `reverse-render-pipeline`

Start with:

- `list_passes`
- `get_frame_packet`

Add when needed:

- `get_pass_packet`
- `inspect_pipeline_state`
- `inspect_shader`

Good stopping point:

- you can propose a likely stage ordering
- you can cite at least one factual signal for each major stage label
