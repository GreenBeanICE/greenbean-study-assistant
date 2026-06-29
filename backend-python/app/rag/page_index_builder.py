from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.entities import DocumentUnit, Section

HEADING_CONFIDENCE_THRESHOLD = 0.4


@dataclass
class SectionBuildResult:
    sections: list[Section] = field(default_factory=list)
    section_unit_links: dict[str, list[str]] = field(default_factory=dict)


def _normalize_headings(unit: DocumentUnit) -> list[dict[str, Any]]:
    raw_headings = (unit.metadata_json or {}).get("headings") or []
    normalized: list[dict[str, Any]] = []

    for heading in raw_headings:
        if not isinstance(heading, dict):
            continue
        title = heading.get("title") or heading.get("text")
        if not title:
            continue
        level = int(heading.get("level") or 1)
        # 使用 get 的默认值，而不是 `or`，避免 confidence=0 被错误处理
        confidence = float(heading.get("confidence", 0.5))
        normalized.append({"title": str(title), "level": max(level, 1), "confidence": confidence})

    return normalized


def _fallback_title(unit: DocumentUnit) -> tuple[str, str, str]:
    metadata = unit.metadata_json or {}
    source_type = str(metadata.get("source_type") or "other")

    if source_type == "ppt" and unit.page_number is not None:
        return f"第 {unit.page_number} 张幻灯片", "slide", "slide"
    if unit.page_number is not None:
        return f"第 {unit.page_number} 页", "page", "page"
    return f"第 {unit.sequence_index + 1} 段", "paragraph", "paragraph"


def _make_metadata(unit: DocumentUnit, **extra: Any) -> dict[str, Any]:
    metadata = dict(unit.metadata_json or {})
    metadata.update(extra)
    return metadata


def _create_section(
    document_id: str,
    title: str,
    level: int,
    order_index: int,
    unit: DocumentUnit,
    *,
    parent_section_id: str | None = None,
    metadata_json: dict[str, Any] | None = None,
) -> Section:
    return Section(
        document_id=document_id,
        parent_section_id=parent_section_id,
        title=title,
        level=level,
        order_index=order_index,
        start_page=unit.page_number,
        end_page=unit.page_number,
        metadata_json=metadata_json,
    )


def _create_fallback_section(document_id: str, unit: DocumentUnit, order_index: int) -> Section:
    title, fallback_kind, node_kind = _fallback_title(unit)
    return _create_section(
        document_id,
        title,
        1,
        order_index,
        unit,
        metadata_json=_make_metadata(unit, fallback_kind=fallback_kind, node_kind=node_kind),
    )


def _extend_section_range(section: Section, page_number: int | None) -> None:
    if page_number is None:
        return
    if section.start_page is None or page_number < section.start_page:
        section.start_page = page_number
    if section.end_page is None or page_number > section.end_page:
        section.end_page = page_number


def _append_links(result: SectionBuildResult, sections: list[Section], unit: DocumentUnit) -> None:
    for section in sections:
        _extend_section_range(section, unit.page_number)
        result.section_unit_links.setdefault(section.id, []).append(unit.id)


def _unique_sections(sections: list[Section]) -> list[Section]:
    unique: list[Section] = []
    seen_ids: set[str] = set()
    for section in sections:
        if section.id in seen_ids:
            continue
        seen_ids.add(section.id)
        unique.append(section)
    return unique


def _create_sections_for_headings(
    document_id: str,
    unit: DocumentUnit,
    headings: list[dict[str, Any]],
    result: SectionBuildResult,
    level_stack: list[Section],
) -> list[Section]:
    created_sections: list[Section] = []

    for heading in headings:
        level = int(heading["level"])
        while level_stack and level_stack[-1].level >= level:
            level_stack.pop()

        parent = level_stack[-1] if level_stack else None
        metadata = _make_metadata(
            unit,
            fallback_kind=None,
            node_kind="slide" if (unit.metadata_json or {}).get("source_type") == "ppt" else "heading",
        )
        section = _create_section(
            document_id,
            heading["title"],
            level,
            len(result.sections),
            unit,
            parent_section_id=parent.id if parent else None,
            metadata_json=metadata,
        )
        result.sections.append(section)
        level_stack.append(section)
        created_sections.append(section)

    return created_sections


def _collect_heading_candidates(units: list[DocumentUnit], confidence_threshold: float = HEADING_CONFIDENCE_THRESHOLD) -> bool:
    """检查所有 units 是否有任何通过置信度阈值的 heading 候选。"""
    for unit in units:
        headings = _normalize_headings(unit)
        for heading in headings:
            if heading.get("confidence", 0) >= confidence_threshold:
                return True
    return False


def build_sections_from_units(document_id: str, units: list[DocumentUnit]) -> SectionBuildResult:
    result = SectionBuildResult()
    if not units:
        return result

    # 检查是否有通过置信度阈值的 heading 候选
    has_heading_candidates = _collect_heading_candidates(units)

    # 如果没有 heading 候选，对 PDF/PPT 按页生成 fallback sections
    if not has_heading_candidates:
        for unit in units:
            fallback_section = _create_fallback_section(document_id, unit, len(result.sections))
            result.sections.append(fallback_section)
            result.section_unit_links.setdefault(fallback_section.id, []).append(unit.id)
        return result

    # 有 heading 候选时，按 level 构建树
    level_stack: list[Section] = []
    active_sections: list[Section] = []

    for unit in units:
        headings = _normalize_headings(unit)
        # 过滤低置信度候选
        valid_headings = [h for h in headings if h.get("confidence", 0) >= HEADING_CONFIDENCE_THRESHOLD]

        if valid_headings:
            active_sections = _create_sections_for_headings(document_id, unit, valid_headings, result, level_stack)
            inherited_sections = [*level_stack[:-1], *active_sections] if level_stack else active_sections
            unique_sections = _unique_sections(inherited_sections)
            _append_links(result, unique_sections, unit)
        elif active_sections:
            # 没有新 heading，挂接到当前活跃 section
            inherited_sections = [*level_stack[:-1], *active_sections] if level_stack else []
            unique_sections = _unique_sections(inherited_sections)
            _append_links(result, unique_sections, unit)
        else:
            # 没有活跃 section，创建 fallback
            fallback_section = _create_fallback_section(document_id, unit, len(result.sections))
            result.sections.append(fallback_section)
            result.section_unit_links.setdefault(fallback_section.id, []).append(unit.id)

    return result
