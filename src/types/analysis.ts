export interface AnalysisSourceRef {
  page: number | null;
  title: string | null;
}

export interface AnalysisTermEntry {
  fr: string;
  zh: string;
  explanation: string;
}

export interface SectionAnalysisContent {
  summary: string;
  key_concepts: string[];
  terms: AnalysisTermEntry[];
  highlights: string[];
  source_refs: AnalysisSourceRef[];
}

export interface SectionAnalysisResponse {
  id: string;
  document_id: string;
  section_id: string;
  analysis_type: string;
  language: string;
  content_markdown: string;
  content_json: SectionAnalysisContent | null;
  source_refs: AnalysisSourceRef[];
  created_at: string;
  updated_at: string;
}

export interface GenerateSectionAnalysisPayload {
  language?: string;
  force_regenerate?: boolean;
}

export type SectionAnalysisQueryResponse = SectionAnalysisResponse | null;
