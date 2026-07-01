import type { SectionNode } from "../../../types/section";

export type OutlineCandidateSource = "pdf_outline" | "llm_outline";
export type OutlineCandidateStatus = "available" | "unavailable";

export interface OutlineCandidateSection {
  tempId: string;
  title: string;
  level: number;
  parentTempId: string | null;
  startPage: number;
  endPage: number;
  orderIndex: number;
}

export interface OutlineCandidate {
  id: string;
  source: OutlineCandidateSource;
  status: OutlineCandidateStatus;
  reason?: string | null;
  sections: OutlineCandidateSection[];
}

export interface UploadedDocument {
  documentId: string;
  filename: string;
  pageCount: number;
  status: string;
  pageIndex: {
    documentId: string;
    pageCount: number;
    pages: unknown[];
  };
  outlineCandidates: OutlineCandidate[];
}

export interface ConfirmOutlineResult {
  sections: SectionNode[];
  sectionUnitLinksStatus: string;
  chunkStatus: string;
  embeddingStatus: string;
}

interface ApiOutlineCandidateSection {
  temp_id: string;
  title: string;
  level: number;
  parent_temp_id: string | null;
  start_page: number;
  end_page: number;
  order_index: number;
}

interface ApiOutlineCandidate {
  id: string;
  source: OutlineCandidateSource;
  status: OutlineCandidateStatus;
  reason?: string | null;
  sections: ApiOutlineCandidateSection[];
}

interface UploadApiResponse {
  code: number;
  data: {
    document_id: string;
    filename: string;
    page_count: number;
    status: string;
    page_index: {
      document_id: string;
      page_count: number;
      pages: unknown[];
    };
    outline_candidates: ApiOutlineCandidate[];
  };
}

interface ConfirmApiResponse {
  code: number;
  data: {
    sections: Array<{
      id: string;
      title: string;
      level: number;
      order_index: number;
      parent_section_id: string | null;
    }>;
    section_unit_links_status: string;
    chunk_status: string;
    embedding_status: string;
  };
}

export async function uploadDocument(file: File): Promise<UploadedDocument> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("/api/documents/upload", {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(`Document upload failed: ${response.status}`);
  }
  const payload = (await response.json()) as UploadApiResponse;
  return {
    documentId: payload.data.document_id,
    filename: payload.data.filename,
    pageCount: payload.data.page_count,
    status: payload.data.status,
    pageIndex: {
      documentId: payload.data.page_index.document_id,
      pageCount: payload.data.page_index.page_count,
      pages: payload.data.page_index.pages,
    },
    outlineCandidates: payload.data.outline_candidates.map(mapCandidate),
  };
}

export async function confirmOutlineCandidate(
  documentId: string,
  candidate: OutlineCandidate,
): Promise<ConfirmOutlineResult> {
  const response = await fetch(`/api/documents/${encodeURIComponent(documentId)}/outline/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ candidate: toApiCandidate(candidate) }),
  });
  if (!response.ok) {
    throw new Error(`Outline confirmation failed: ${response.status}`);
  }
  const payload = (await response.json()) as ConfirmApiResponse;
  return {
    sections: toSectionTree(payload.data.sections),
    sectionUnitLinksStatus: payload.data.section_unit_links_status,
    chunkStatus: payload.data.chunk_status,
    embeddingStatus: payload.data.embedding_status,
  };
}

function mapCandidate(candidate: ApiOutlineCandidate): OutlineCandidate {
  return {
    id: candidate.id,
    source: candidate.source,
    status: candidate.status,
    reason: candidate.reason ?? null,
    sections: candidate.sections.map((section) => ({
      tempId: section.temp_id,
      title: section.title,
      level: section.level,
      parentTempId: section.parent_temp_id,
      startPage: section.start_page,
      endPage: section.end_page,
      orderIndex: section.order_index,
    })),
  };
}

function toApiCandidate(candidate: OutlineCandidate): ApiOutlineCandidate {
  return {
    id: candidate.id,
    source: candidate.source,
    status: candidate.status,
    reason: candidate.reason ?? null,
    sections: candidate.sections.map((section) => ({
      temp_id: section.tempId,
      title: section.title,
      level: section.level,
      parent_temp_id: section.parentTempId,
      start_page: section.startPage,
      end_page: section.endPage,
      order_index: section.orderIndex,
    })),
  };
}

function toSectionTree(
  sections: ConfirmApiResponse["data"]["sections"],
): SectionNode[] {
  type SectionNodeWithParent = SectionNode & {
    parentSectionId: string | null;
    children?: SectionNodeWithParent[];
  };
  const nodes: SectionNodeWithParent[] = sections.map((section, index) => ({
    id: section.id,
    title: section.title,
    index: String(section.order_index + 1 || index + 1),
    expanded: true,
    parentSectionId: section.parent_section_id,
  }));
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const roots: SectionNode[] = [];
  nodes.forEach((node) => {
    const parentId = node.parentSectionId;
    if (parentId && byId.has(parentId)) {
      const parent = byId.get(parentId)!;
      parent.children = [...(parent.children ?? []), node];
    } else {
      roots.push(node);
    }
  });
  return roots;
}
