from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def text(value: Any, default: str = "unknown") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    value = str(value).strip()
    return value or default


def bullet_from_item(item: Any) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return text(item)
    parts: list[str] = []
    if item.get("label"):
        parts.append(str(item["label"]))
    if item.get("slot") is not None:
        parts.append(f"slot={item['slot']}")
    if item.get("rid"):
        parts.append(f"rid={item['rid']}")
    if item.get("name"):
        parts.append(f"name={item['name']}")
    if item.get("fmt"):
        parts.append(f"fmt={item['fmt']}")
    if item.get("dims"):
        parts.append(f"dims={item['dims']}")
    if item.get("role"):
        parts.append(f"role={item['role']}")
    if item.get("status"):
        parts.append(f"status={item['status']}")
    if item.get("path"):
        parts.append(f"path={item['path']}")
    if item.get("note"):
        parts.append(str(item["note"]))
    if not parts:
        parts.append(json.dumps(item, ensure_ascii=False))
    return " | ".join(parts)


def emit_list_section(lines: list[str], title: str, items: list[Any], empty_text: str | None = None) -> None:
    lines.append(f"## {title}")
    lines.append("")
    if items:
        for item in items:
            lines.append(f"- {bullet_from_item(item)}")
    elif empty_text:
        lines.append(f"- {empty_text}")
    lines.append("")


def emit_table_section(
    lines: list[str],
    title: str,
    columns: list[tuple[str, str]],
    rows: list[dict[str, Any]],
    empty_text: str | None = None,
) -> None:
    lines.append(f"## {title}")
    lines.append("")
    if not rows:
        if empty_text:
            lines.append(f"- {empty_text}")
            lines.append("")
        return
    headers = [label for _, label in columns]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for row in rows:
        values = [text(row.get(key), "") for key, _ in columns]
        lines.append("| " + " | ".join(values) + " |")
    lines.append("")


def render_code_block(block: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    stage = text(block.get("stage"), "").upper()
    title = text(block.get("title"), "Unnamed Block")
    line_range = text(block.get("line_range"), "")
    heading = "### "
    if stage and line_range:
        heading += f"{stage} {line_range} - {title}"
    elif stage:
        heading += f"{stage} - {title}"
    elif line_range:
        heading += f"{line_range} - {title}"
    else:
        heading += title
    lines.append(heading)
    lines.append("")

    snippet = block.get("snippet")
    if snippet:
        lines.append("```hlsl")
        lines.append(str(snippet).rstrip())
        lines.append("```")
        lines.append("")

    summary = as_list(block.get("summary"))
    confirmed = as_list(block.get("confirmed"))
    uncertain = as_list(block.get("uncertain"))
    evidence_level = block.get("evidence_level")

    if evidence_level:
        lines.append(f"- evidence level: {text(evidence_level)}")
    for item in summary:
        lines.append(f"- summary: {text(item)}")
    for item in confirmed:
        lines.append(f"- confirmed: {text(item)}")
    for item in uncertain:
        lines.append(f"- uncertain: {text(item)}")
    lines.append("")
    return lines


def render_report(bundle: dict[str, Any], working_dir: Path) -> str:
    action = bundle.get("action") or {}
    artifacts = bundle.get("artifacts") or {}
    geometry = bundle.get("geometry") or {}
    resource_inventory = bundle.get("resource_inventory") or {}
    metadata_candidates = as_list(bundle.get("metadata_candidates"))
    runtime_cbuffer = as_list(bundle.get("runtime_cbuffer"))
    code_blocks = as_list(bundle.get("code_blocks"))
    outputs = as_list(bundle.get("outputs"))
    chain = as_list(bundle.get("producer_consumer_chain") or bundle.get("downstream"))
    image_evidence = as_list((bundle.get("images") or {}).get("items")) + as_list(bundle.get("image_evidence"))
    probes = as_list(bundle.get("probes"))
    human_review = as_list(bundle.get("human_review"))
    validation = bundle.get("validation") or {}

    lines: list[str] = []
    lines.append(
        "Action: {eid} {name} ({kind})".format(
            eid=text(action.get("eid")),
            name=text(action.get("name")),
            kind=text(action.get("kind"), "unknown"),
        )
    )
    lines.append(f"Capture: {text(action.get('capture_path'))}")
    lines.append(f"Marker Path: {text(action.get('marker_path'))}")
    lines.append(f"Parent Pass: {text(action.get('parent_pass'))}")
    lines.append(f"Root Pass: {text(action.get('root_pass'))}")
    lines.append(f"Position: {text(action.get('position'))}")
    neighbors = action.get("neighbors") or {}
    lines.append(f"Neighbors: prev={text(neighbors.get('prev'))} next={text(neighbors.get('next'))}")
    lines.append("")

    hlsl_rows = []
    for item in as_list(artifacts.get("hlsl")):
        if isinstance(item, dict):
            hlsl_rows.append(
                {
                    "stage": text(item.get("stage"), ""),
                    "raw": text(item.get("raw"), ""),
                    "annotated": text(item.get("annotated") or item.get("notes"), ""),
                }
            )
    artifact_rows = []
    for row in hlsl_rows:
        artifact_rows.append(
            {
                "artifact": f"{row['stage']} raw HLSL",
                "path": row["raw"],
            }
        )
        if row["annotated"]:
            artifact_rows.append(
                {
                    "artifact": f"{row['stage']} annotated HLSL",
                    "path": row["annotated"],
                }
            )
    artifact_rows.append({"artifact": "report dir", "path": str(working_dir)})
    emit_table_section(lines, "Artifacts", [("artifact", "Artifact"), ("path", "Path")], artifact_rows)

    geometry_items = as_list(geometry.get("summary"))
    if geometry.get("topology") or geometry.get("index_count") or geometry.get("instance_count"):
        geometry_items = [
            {
                "label": "geometry",
                "note": "topology={topology} index_count={idx} instance_count={inst}".format(
                    topology=text(geometry.get("topology"), "unknown"),
                    idx=text(geometry.get("index_count"), "unknown"),
                    inst=text(geometry.get("instance_count"), "unknown"),
                ),
            }
        ] + geometry_items
    geometry_items += as_list(geometry.get("bindings"))
    emit_list_section(lines, "Geometry", geometry_items, "not applicable or not yet recorded")

    binding_items: list[Any] = []
    for stage_name in ("VS", "PS", "CS"):
        stage_items = as_list(resource_inventory.get(stage_name))
        for item in stage_items:
            if isinstance(item, dict):
                entry = dict(item)
                entry.setdefault("label", stage_name)
                binding_items.append(entry)
            else:
                binding_items.append({"label": stage_name, "note": text(item)})
    emit_list_section(lines, "Bindings", binding_items, "no bindings recorded")

    if metadata_candidates:
        emit_table_section(
            lines,
            "Metadata Candidates",
            [
                ("symbol", "Symbol"),
                ("property", "Property"),
                ("source", "Source"),
                ("status", "Status"),
                ("note", "Note"),
            ],
            [item if isinstance(item, dict) else {"note": text(item)} for item in metadata_candidates],
        )
    else:
        emit_list_section(lines, "Metadata Candidates", [], "metadata unavailable or no useful candidates")

    runtime_rows: list[dict[str, Any]] = []
    for block in runtime_cbuffer:
        if isinstance(block, dict) and block.get("rows"):
            for row in as_list(block.get("rows")):
                if isinstance(row, dict):
                    runtime_rows.append(
                        {
                            "slot": text(block.get("slot") or block.get("name"), ""),
                            "symbol": text(row.get("symbol")),
                            "value": text(row.get("value")),
                            "candidate": text(row.get("candidate"), ""),
                            "status": text(row.get("status"), ""),
                        }
                    )
        elif isinstance(block, dict):
            runtime_rows.append(
                {
                    "slot": text(block.get("slot") or block.get("name"), ""),
                    "symbol": text(block.get("symbol")),
                    "value": text(block.get("value")),
                    "candidate": text(block.get("candidate"), ""),
                    "status": text(block.get("status"), ""),
                }
            )
    emit_table_section(
        lines,
        "Runtime CBuffer Checks",
        [
            ("slot", "Slot"),
            ("symbol", "Symbol"),
            ("value", "Runtime Value"),
            ("candidate", "Candidate"),
            ("status", "Status"),
        ],
        runtime_rows,
        "no runtime cbuffer checks recorded",
    )

    lines.append("## Code Blocks")
    lines.append("")
    if code_blocks:
        for block in code_blocks:
            if isinstance(block, dict):
                lines.extend(render_code_block(block))
            else:
                lines.append(f"- {text(block)}")
                lines.append("")
    else:
        lines.append("- no code blocks recorded")
        lines.append("")

    emit_table_section(
        lines,
        "Outputs",
        [
            ("target", "Target"),
            ("resource", "Resource"),
            ("consumer", "Consumer"),
            ("semantics", "Semantics"),
            ("evidence_level", "Evidence Level"),
        ],
        [
            {
                "target": text(item.get("target")),
                "resource": text(item.get("resource") or item.get("rid")),
                "consumer": text(item.get("consumer")),
                "semantics": "; ".join(text(v, "") for v in as_list(item.get("semantics")) if text(v, "")),
                "evidence_level": text(item.get("evidence_level"), ""),
            }
            if isinstance(item, dict)
            else {"semantics": text(item)}
            for item in outputs
        ],
        "no outputs recorded",
    )

    emit_list_section(lines, "Producer / Consumer Chain", chain, "no producer or consumer chain recorded")
    emit_list_section(lines, "Image Evidence", image_evidence, "no image evidence recorded")
    emit_list_section(lines, "Probe Evidence", probes, "no shader-edit probes recorded")

    conclusion_items = as_list(bundle.get("conclusion"))
    emit_list_section(lines, "Conclusion", conclusion_items, "no conclusion recorded")

    human_review_items = []
    for item in human_review:
        if isinstance(item, dict):
            human_review_items.append(
                {
                    "label": text(item.get("id")),
                    "note": "topic={topic} image={image} hypothesis={hypothesis} level={level}".format(
                        topic=text(item.get("topic"), ""),
                        image=text(item.get("image"), ""),
                        hypothesis=text(item.get("current_hypothesis") or item.get("hypothesis"), ""),
                        level=text(item.get("evidence_level"), ""),
                    ),
                }
            )
        else:
            human_review_items.append(item)
    emit_list_section(lines, "Human Review", human_review_items, "no unresolved semantics remain")

    validation_items: list[Any] = []
    for item in as_list(validation.get("compile")):
        if isinstance(item, dict):
            validation_items.append(
                {
                    "label": "compile",
                    "note": "stage={stage} profile={profile} result={result} command={command}".format(
                        stage=text(item.get("stage"), ""),
                        profile=text(item.get("profile"), ""),
                        result=text(item.get("result"), ""),
                        command=text(item.get("command"), ""),
                    ),
                }
            )
        else:
            validation_items.append(item)
    validation_items += as_list(validation.get("checks"))
    emit_list_section(lines, "Validation", validation_items, "no validation recorded")

    return "\n".join(lines).rstrip() + "\n"


def render_human_review(bundle: dict[str, Any]) -> str:
    items = as_list(bundle.get("human_review"))
    lines: list[str] = ["# Needs Human Review", ""]
    if not items:
        lines.append("- No unresolved semantics remain.")
        lines.append("")
        return "\n".join(lines)

    for item in items:
        if isinstance(item, dict):
            lines.append(f"## {text(item.get('id'), 'review-item')}")
            lines.append("")
            lines.append(f"- topic: {text(item.get('topic'))}")
            lines.append(f"- image: {text(item.get('image'))}")
            lines.append(f"- current hypothesis: {text(item.get('current_hypothesis') or item.get('hypothesis'))}")
            lines.append(f"- evidence level: {text(item.get('evidence_level'))}")
            lines.append(f"- why unresolved: {text(item.get('why_unresolved'))}")
            lines.append(f"- suggested next probe: {text(item.get('suggested_next_probe'))}")
            lines.append("")
        else:
            lines.append(f"- {text(item)}")
    return "\n".join(lines).rstrip() + "\n"


def resolve_working_dir(bundle: dict[str, Any], out_dir_arg: str | None) -> Path | None:
    if out_dir_arg:
        return Path(out_dir_arg)
    artifacts = bundle.get("artifacts") or {}
    working_dir = artifacts.get("working_dir")
    if working_dir:
        return Path(str(working_dir))
    return None


def ensure_layout(working_dir: Path) -> None:
    working_dir.mkdir(parents=True, exist_ok=True)
    (working_dir / "assets").mkdir(parents=True, exist_ok=True)
    (working_dir / "debug_shaders").mkdir(parents=True, exist_ok=True)
    (working_dir / "review").mkdir(parents=True, exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a strict shader-restoration report from a reverse-action bundle."
    )
    parser.add_argument("--bundle", required=True, help="JSON bundle with action restoration evidence.")
    parser.add_argument("--out-dir", help="Working directory. Defaults to bundle.artifacts.working_dir.")
    parser.add_argument("--out", help="Report path. Defaults to <working_dir>/Action_Restore_Report.md.")
    parser.add_argument(
        "--review-out",
        help="Human-review path. Defaults to <working_dir>/review/needs_human_review.md.",
    )
    args = parser.parse_args()

    bundle = load_json(args.bundle)
    working_dir = resolve_working_dir(bundle, args.out_dir)
    report_text: str
    review_text: str

    if working_dir is not None:
        ensure_layout(working_dir)
        report_text = render_report(bundle, working_dir)
        review_text = render_human_review(bundle)

        report_path = Path(args.out) if args.out else working_dir / "Action_Restore_Report.md"
        review_path = Path(args.review_out) if args.review_out else working_dir / "review" / "needs_human_review.md"

        report_path.write_text(report_text, encoding="utf-8")
        review_path.write_text(review_text, encoding="utf-8")
        print(str(report_path))
        return 0

    report_text = render_report(bundle, Path("."))
    if args.out:
        Path(args.out).write_text(report_text, encoding="utf-8")
    else:
        print(report_text, end="")
    if args.review_out:
        Path(args.review_out).write_text(render_human_review(bundle), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
