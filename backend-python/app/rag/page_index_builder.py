from app.entities import DocumentUnit, Section


def _fallback_title(unit: DocumentUnit) -> str:
    if unit.page_number is not None:
        return f"Page {unit.page_number}"
    return f"Unit {unit.sequence_index + 1}"


def build_sections_from_units(document_id: str, units: list[DocumentUnit]) -> list[Section]:
    sections: list[Section] = []
    for unit in units:
        headings = (unit.metadata_json or {}).get("headings") or []
        heading = headings[0] if headings else {}
        title = heading.get("title") or _fallback_title(unit)
        level = int(heading.get("level") or 1)

        sections.append(
            Section(
                document_id=document_id,
                title=title,
                level=level,
                order_index=len(sections),
                start_page=unit.page_number,
                end_page=unit.page_number,
                metadata_json={"source_unit_id": unit.id},
            )
        )
    return sections
