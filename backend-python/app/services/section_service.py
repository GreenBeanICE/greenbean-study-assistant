from __future__ import annotations

import re

from pydantic import BaseModel, Field

from app.entities import Section, SectionUnitLink
from app.rag.page_index_builder import build_sections_from_units


class SectionTreeNode(BaseModel):
    id: str
    title: str
    level: int
    order_index: int
    start_page: int | None = None
    end_page: int | None = None
    children: list["SectionTreeNode"] = Field(default_factory=list)


class SectionService:
    def __init__(self, uow_factory) -> None:
        self.uow_factory = uow_factory

    @staticmethod
    def _is_legacy_page_title(title: str) -> bool:
        # 匹配旧格式 "Page N" / "Unit N" 和新格式 "第 N 页"
        return bool(re.fullmatch(r"(?:Page|Unit)\s+\d+|第\s*\d+\s*页", title))

    def _is_legacy_page_sections(self, sections: list[Section]) -> bool:
        return bool(sections) and all(
            self._is_legacy_page_title(section.title) and section.parent_section_id is None
            for section in sections
        )

    def build_sections(self, document_id: str) -> list[Section]:
        from app.repositories.document_unit_repository import DocumentUnitRepository
        from app.repositories.section_repository import SectionRepository
        from app.repositories.section_unit_link_repository import SectionUnitLinkRepository

        with self.uow_factory() as uow:
            section_repo = SectionRepository(uow.session)
            link_repo = SectionUnitLinkRepository(uow.session)
            existing = section_repo.list_by_document(document_id)
            if existing and not self._is_legacy_page_sections(existing):
                return existing

            if existing:
                link_repo.delete_by_document(document_id)
                section_repo.delete_by_document(document_id)

            units = DocumentUnitRepository(uow.session).list_by_document(document_id)
            build_result = build_sections_from_units(document_id, units)
            for section in build_result.sections:
                section_repo.save(section)
                for order_index, unit_id in enumerate(build_result.section_unit_links.get(section.id, [])):
                    link_repo.save(
                        SectionUnitLink(
                            section_id=section.id,
                            document_unit_id=unit_id,
                            order_index=order_index,
                        )
                    )
            uow.commit()
            return build_result.sections

    def get_section_tree(self, document_id: str) -> list[SectionTreeNode]:
        from app.repositories.section_repository import SectionRepository

        with self.uow_factory() as uow:
            sections = SectionRepository(uow.session).list_by_document(document_id)

        nodes = {
            section.id: SectionTreeNode(
                id=section.id,
                title=section.title,
                level=section.level,
                order_index=section.order_index,
                start_page=section.start_page,
                end_page=section.end_page,
            )
            for section in sections
        }
        roots: list[SectionTreeNode] = []
        for section in sections:
            node = nodes[section.id]
            if section.parent_section_id and section.parent_section_id in nodes:
                nodes[section.parent_section_id].children.append(node)
            else:
                roots.append(node)
        return roots

    def get_section_content(self, section_id: str):
        from app.repositories.document_unit_repository import DocumentUnitRepository
        from app.repositories.section_repository import SectionRepository
        from app.repositories.section_unit_link_repository import SectionUnitLinkRepository

        with self.uow_factory() as uow:
            section = SectionRepository(uow.session).get_by_id(section_id)
            if section is None:
                raise ValueError(f"Section not found: {section_id}")

            links = SectionUnitLinkRepository(uow.session).list_by_section(section_id)
            if links:
                units = DocumentUnitRepository(uow.session).list_by_ids(
                    [link.document_unit_id for link in links]
                )
                return {
                    "anchor_unit_id": units[0].id if units else None,
                    "units": units,
                }

            units = DocumentUnitRepository(uow.session).list_by_document(section.document_id)
            if section.start_page is None:
                return {
                    "anchor_unit_id": units[0].id if units else None,
                    "units": units,
                }
            end_page = section.end_page or section.start_page
            filtered_units = [
                unit
                for unit in units
                if unit.page_number is not None and section.start_page <= unit.page_number <= end_page
            ]
            return {
                "anchor_unit_id": filtered_units[0].id if filtered_units else None,
                "units": filtered_units,
            }

    def get_section_by_id(self, section_id: str):
        from app.repositories.section_repository import SectionRepository

        with self.uow_factory() as uow:
            return SectionRepository(uow.session).get_by_id(section_id)
