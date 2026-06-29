import { request } from "../../../lib/apiClient";
import type {
  GenerateSectionAnalysisPayload,
  SectionAnalysisQueryResponse,
  SectionAnalysisResponse,
} from "../../../types/analysis";

export function getSectionAnalysis(sectionId: string): Promise<SectionAnalysisQueryResponse> {
  return request(`/analyses/sections/${sectionId}`);
}

export function generateSectionAnalysis(
  sectionId: string,
  payload: GenerateSectionAnalysisPayload = {},
): Promise<SectionAnalysisResponse> {
  return request(`/analyses/sections/${sectionId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      language: payload.language ?? "zh",
      force_regenerate: payload.force_regenerate ?? false,
    }),
  });
}
