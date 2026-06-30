import type { ContentBlock, SourceCitation, SourcePage } from "../../../types/section";

interface ApiSourceCitation {
  id: string;
  page: number | null;
  document_unit_id: string;
  chunk_id?: string | null;
  source_text: string;
  start_char: number;
  end_char: number;
}

interface ApiAnalysisSentence {
  id: string;
  text: string;
  citations: ApiSourceCitation[];
}

interface ApiSourcePage {
  page: number | null;
  document_unit_id: string;
  text: string;
}

interface ApiSectionAnalysisOutput {
  section_id: string;
  section_title: string;
  status: "draft" | "completed";
  sentences: ApiAnalysisSentence[];
  source_pages: ApiSourcePage[];
}

interface ApiAnalysisResponse {
  code: number;
  message: string;
  data: {
    section_id: string;
    content_json: ApiSectionAnalysisOutput;
  };
}

interface ApiErrorDetail {
  code?: string;
  message?: string;
}

interface ApiErrorResponse {
  detail?: string | ApiErrorDetail;
}

export interface SectionAnalysisViewModel {
  contentBlock: ContentBlock;
  sourcePages: SourcePage[];
}

export class SectionAnalysisApiError extends Error {
  readonly status: number;
  readonly code: string | null;

  constructor(message: string, options: { status: number; code?: string | null }) {
    super(message);
    this.name = "SectionAnalysisApiError";
    this.status = options.status;
    this.code = options.code ?? null;
  }
}

export async function analyzeSection(sectionId: string): Promise<SectionAnalysisViewModel> {
  const response = await fetch(`/api/analysis/sections/${encodeURIComponent(sectionId)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      language: "zh",
      prompt_version: "section-analysis-v1",
    }),
  });
  if (!response.ok) {
    throw await buildApiError(response);
  }
  const payload = (await response.json()) as ApiAnalysisResponse;
  return mapSectionAnalysis(payload.data.content_json);
}

async function buildApiError(response: Response): Promise<SectionAnalysisApiError> {
  let payload: ApiErrorResponse | null = null;
  try {
    payload = (await response.json()) as ApiErrorResponse;
  } catch {
    payload = null;
  }
  const detail = payload?.detail;
  if (detail && typeof detail === "object") {
    return new SectionAnalysisApiError(detail.message ?? `Section analysis failed: ${response.status}`, {
      status: response.status,
      code: detail.code ?? null,
    });
  }
  return new SectionAnalysisApiError(
    typeof detail === "string" ? detail : `Section analysis failed: ${response.status}`,
    { status: response.status },
  );
}

function mapSectionAnalysis(output: ApiSectionAnalysisOutput): SectionAnalysisViewModel {
  return {
    contentBlock: {
      id: `block-${output.section_id}`,
      sectionId: output.section_id,
      title: output.section_title,
      contentType: "text",
      lines: output.sentences.map((sentence) => ({
        id: sentence.id,
        text: sentence.text,
        type: "paragraph",
        citations: sentence.citations.map(mapCitation),
      })),
    },
    sourcePages: output.source_pages.map(mapSourcePage),
  };
}

function mapCitation(citation: ApiSourceCitation): SourceCitation {
  return {
    id: citation.id,
    page: citation.page,
    documentUnitId: citation.document_unit_id,
    chunkId: citation.chunk_id ?? null,
    sourceText: citation.source_text,
    startChar: citation.start_char,
    endChar: citation.end_char,
  };
}

function mapSourcePage(page: ApiSourcePage): SourcePage {
  return {
    page: page.page,
    documentUnitId: page.document_unit_id,
    text: page.text,
  };
}
