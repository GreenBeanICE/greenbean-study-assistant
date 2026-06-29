# Section Analysis Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add section-level AI analysis query, generation, frontend display, and final persistence so a selected section can show existing analysis or generate it on demand.

**Architecture:** Implement the feature in three vertical slices that match the approved priority: backend analysis API first, frontend generate-and-display flow second, persistence and reuse last. Keep the backend returning domain analysis data, then map it in the frontend to existing `ContentBlock` structures for `DocumentViewer`.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy/SQLite, existing provider registry, React 19, TypeScript, Vitest, Testing Library.

---

## File Map

- Modify: `backend-python/app/api/analysis_controller.py`
  - Replace the placeholder with section analysis `GET` and `POST` endpoints.
- Modify: `backend-python/app/api/dependencies.py`
  - Add `get_analysis_service()` and wire service construction.
- Modify: `backend-python/app/main.py`
  - Register the new analysis router.
- Modify: `backend-python/app/services/analysis_service.py`
  - Replace the placeholder-oriented helper flow with a section-focused service API.
- Modify: `backend-python/app/services/section_service.py`
  - Add `get_section_by_id()` so analysis generation can resolve the selected section metadata.
- Modify: `backend-python/app/schemas/analysis_schema.py`
  - Add response models and entity-to-response conversion helpers for section analysis.
- Modify: `backend-python/app/repositories/analysis_result_repository.py`
  - Add query helpers for section-level lookup in the persistence slice.
- Create: `backend-python/tests/integration/api/test_analysis_controller.py`
  - Add controller integration coverage for query and generation.
- Modify: `backend-python/tests/unit/services/test_analysis_service.py`
  - Add service behavior coverage for raw-only section analysis generation and reuse.
- Create: `src/features/analysis/api/analysisApi.ts`
  - Add frontend API wrappers for section analysis query and generation.
- Create: `src/features/analysis/analysisToContentBlocks.ts`
  - Convert analysis payloads to `ContentBlock[]` for the existing viewer.
- Create: `src/types/analysis.ts`
  - Add frontend analysis DTO types aligned to backend responses.
- Modify: `src/features/workspace/type.ts`
  - Extend `DocumentViewerProps` with analysis state and generate callback props.
- Modify: `src/features/workspace/components/center/DocumentViewer.tsx`
  - Show generate/retry/loading states in the parsed panel empty area.
- Modify: `src/features/workspace/components/center/DocumentViewer.test.tsx`
  - Cover the new parsed-panel action states.
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`
  - Add section analysis load/generate/cache/persistence-aware orchestration.
- Modify: `src/features/workspace/pages/WorkspacePage.test.tsx`
  - Cover query-existing, generate-new, and retry-failure workflows.

## Task 1: Lock Backend Behavior with Service and API Tests

**Files:**
- Modify: `backend-python/tests/unit/services/test_analysis_service.py`
- Create: `backend-python/tests/integration/api/test_analysis_controller.py`

- [ ] **Step 1: Add failing unit tests for section analysis service behavior**

Append tests like these to `backend-python/tests/unit/services/test_analysis_service.py`:

```python
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.entities.analysis_result import AnalysisResult
from app.enums.analysis_type import AnalysisType
from app.services.analysis_service import AnalysisService


@pytest.mark.asyncio
async def test_generate_section_analysis_uses_raw_units_only():
    section_service = MagicMock()
    section_service.get_section_content.return_value = {
        "anchor_unit_id": "u1",
        "units": [
            SimpleNamespace(id="u1", sequence_index=0, page_number=3, text_content="第一段原文"),
            SimpleNamespace(id="u2", sequence_index=1, page_number=4, text_content="第二段原文"),
        ],
    }
    section_service.get_section_by_id.return_value = SimpleNamespace(
        id="sec-1",
        document_id="doc-1",
        title="1.1 背景介绍",
    )
    agent = MagicMock()
    agent.generate_analysis = AsyncMock(
        return_value={
            "summary": "摘要",
            "key_concepts": ["概念 A"],
            "terms": [],
            "highlights": ["重点 A"],
            "source_refs": [{"page": 3, "title": "1.1 背景介绍"}],
        }
    )
    service = AnalysisService(
        section_service=section_service,
        analysis_agent=agent,
        analysis_result_repository=None,
        uow_factory=None,
    )

    result = await service.generate_section_analysis("sec-1")

    assert isinstance(result, AnalysisResult)
    assert result.document_id == "doc-1"
    assert result.section_id == "sec-1"
    assert result.analysis_type == AnalysisType.SECTION
    called_context = agent.generate_analysis.await_args.args[0]
    assert "第一段原文" in called_context
    assert "第二段原文" in called_context
    assert "chat_messages" not in called_context
    assert "analyses" not in called_context


@pytest.mark.asyncio
async def test_generate_section_analysis_rejects_empty_units():
    section_service = MagicMock()
    section_service.get_section_content.return_value = {
        "anchor_unit_id": None,
        "units": [],
    }
    section_service.get_section_by_id.return_value = SimpleNamespace(
        id="sec-1",
        document_id="doc-1",
        title="1.1 背景介绍",
    )
    service = AnalysisService(
        section_service=section_service,
        analysis_agent=MagicMock(),
        analysis_result_repository=None,
        uow_factory=None,
    )

    with pytest.raises(ValueError) as exc_info:
        await service.generate_section_analysis("sec-1")

    assert "资料依据不足" in str(exc_info.value)
```

- [ ] **Step 2: Add failing integration tests for analysis controller query and generate**

Create `backend-python/tests/integration/api/test_analysis_controller.py` with:

```python
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_analysis_service
from app.main import app


@pytest.fixture
def client():
    analysis_service = MagicMock()
    app.dependency_overrides[get_analysis_service] = lambda: analysis_service
    yield TestClient(app), analysis_service
    app.dependency_overrides.clear()


def test_get_section_analysis_returns_404_when_missing(client):
    test_client, analysis_service = client
    analysis_service.get_section_analysis.return_value = None

    response = test_client.get("/api/analyses/sections/sec-1")

    assert response.status_code == 404


def test_generate_section_analysis_success(client):
    test_client, analysis_service = client
    from app.entities.analysis_result import AnalysisResult
    from app.enums.analysis_type import AnalysisType

    analysis_service.generate_section_analysis = AsyncMock(
        return_value=AnalysisResult(
            document_id="doc-1",
            section_id="sec-1",
            analysis_type=AnalysisType.SECTION,
            language="zh",
            content_markdown="## 中文总结\n\n摘要",
            content_json={
                "summary": "摘要",
                "key_concepts": ["概念 A"],
                "terms": [],
                "highlights": ["重点 A"],
                "source_refs": [{"page": 3, "title": "1.1 背景介绍"}],
            },
            prompt_version="section-v1",
        )
    )

    response = test_client.post(
        "/api/analyses/sections/sec-1/generate",
        json={"language": "zh", "force_regenerate": False},
    )

    assert response.status_code == 200
    assert response.json()["data"]["section_id"] == "sec-1"
    assert response.json()["data"]["content_json"]["summary"] == "摘要"
```

- [ ] **Step 3: Run the new backend tests and verify Red**

Run: `rtk pytest backend-python/tests/unit/services/test_analysis_service.py backend-python/tests/integration/api/test_analysis_controller.py -q`

Expected: FAIL because `AnalysisService` does not yet expose `generate_section_analysis`, `analysis_controller.py` is still a placeholder, and the router is not registered.

## Task 2: Implement the Backend Section Analysis API Slice

**Files:**
- Modify: `backend-python/app/api/analysis_controller.py`
- Modify: `backend-python/app/api/dependencies.py`
- Modify: `backend-python/app/main.py`
- Modify: `backend-python/app/services/analysis_service.py`
- Modify: `backend-python/app/services/section_service.py`
- Modify: `backend-python/app/schemas/analysis_schema.py`

- [ ] **Step 1: Replace the placeholder controller with section analysis endpoints**

Implement `backend-python/app/api/analysis_controller.py` like this:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_analysis_service
from app.schemas.analysis_schema import (
    SectionAnalysisGenerateRequest,
    SectionAnalysisResponse,
)
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.get("/sections/{section_id}")
def get_section_analysis(
    section_id: str,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
):
    result = service.get_section_analysis(section_id)
    if result is None:
        raise HTTPException(status_code=404, detail="该章节暂无解析")
    return {"code": 200, "data": SectionAnalysisResponse.from_entity(result)}


@router.post("/sections/{section_id}/generate")
async def generate_section_analysis(
    section_id: str,
    payload: SectionAnalysisGenerateRequest,
    service: Annotated[AnalysisService, Depends(get_analysis_service)],
):
    try:
        result = await service.generate_section_analysis(
            section_id,
            language=payload.language,
            force_regenerate=payload.force_regenerate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"code": 200, "data": SectionAnalysisResponse.from_entity(result)}
```

- [ ] **Step 2: Add request/response models for section analysis**

Extend `backend-python/app/schemas/analysis_schema.py` with:

```python
class SourceRefResponse(BaseModel):
    page: int | None = None
    title: str | None = None


class SectionAnalysisGenerateRequest(BaseModel):
    language: str = Field(default="zh", description="分析结果输出语言。")
    force_regenerate: bool = Field(default=False, description="是否强制重新生成解析。")


class SectionAnalysisResponse(BaseModel):
    id: str
    document_id: str
    section_id: str
    analysis_type: AnalysisType
    language: str
    content_markdown: str
    content_json: dict | None = None
    source_refs: list[SourceRefResponse] = Field(default_factory=list)
    model_name: str | None = None
    prompt_version: str | None = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, result: AnalysisResult) -> "SectionAnalysisResponse":
        refs = []
        if result.content_json and isinstance(result.content_json.get("source_refs"), list):
            refs = [SourceRefResponse.model_validate(item) for item in result.content_json["source_refs"]]
        return cls(
            id=result.id,
            document_id=result.document_id,
            section_id=result.section_id or "",
            analysis_type=result.analysis_type,
            language=result.language,
            content_markdown=result.content_markdown,
            content_json=result.content_json,
            source_refs=refs,
            model_name=result.model_name,
            prompt_version=result.prompt_version,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
```

- [ ] **Step 3: Replace the placeholder service helpers with a section-focused service class**

Refactor `backend-python/app/services/analysis_service.py` to keep `build_markdown_from_json()` and add:

```python
from app.agents.analysis_agent import AnalysisAgent
from app.entities.analysis_result import AnalysisResult
from app.enums.analysis_type import AnalysisType


class AnalysisService:
    def __init__(
        self,
        *,
        section_service,
        analysis_agent: AnalysisAgent | None = None,
        analysis_result_repository=None,
        uow_factory=None,
    ) -> None:
        self.section_service = section_service
        self.analysis_agent = analysis_agent or AnalysisAgent()
        self.analysis_result_repository = analysis_result_repository
        self.uow_factory = uow_factory

    def get_section_analysis(self, section_id: str):
        if self.analysis_result_repository is None:
            return None
        return self.analysis_result_repository.get_by_section_id(section_id)

    async def generate_section_analysis(
        self,
        section_id: str,
        *,
        language: str = "zh",
        force_regenerate: bool = False,
    ) -> AnalysisResult:
        if not force_regenerate:
            existing = self.get_section_analysis(section_id)
            if existing is not None:
                return existing

        section = self.section_service.get_section_by_id(section_id)
        if section is None:
            raise ValueError(f"Section not found: {section_id}")

        content = self.section_service.get_section_content(section_id)
        units = [unit for unit in content["units"] if unit.text_content.strip()]
        if not units:
            raise ValueError("资料依据不足：该章节当前没有可用于生成解析的原文")

        document_context = self._build_section_context(section.title, units)
        analysis_data = await self.analysis_agent.generate_analysis(document_context)
        markdown_text = build_markdown_from_json(analysis_data)
        return AnalysisResult(
            document_id=section.document_id,
            section_id=section.id,
            analysis_type=AnalysisType.SECTION,
            language=language,
            content_markdown=markdown_text,
            content_json=analysis_data,
            prompt_version="section-v1",
        )

    @staticmethod
    def _build_section_context(section_title: str, units) -> str:
        lines: list[str] = [f"章节标题: {section_title}"]
        for unit in units:
            page_desc = f"第 {unit.page_number} 页" if unit.page_number is not None else f"单元 {unit.sequence_index + 1}"
            lines.append(f"[{page_desc}]\n{unit.text_content}")
        return "\n\n".join(lines)
```

- [ ] **Step 4: Add a small section lookup helper used by analysis generation**

Add this method to `backend-python/app/services/section_service.py`:

```python
    def get_section_by_id(self, section_id: str):
        from app.repositories.section_repository import SectionRepository

        with self.uow_factory() as uow:
            return SectionRepository(uow.session).get_by_id(section_id)
```

- [ ] **Step 5: Wire the service into dependencies and FastAPI startup**

Update `backend-python/app/api/dependencies.py`:

```python
from app.services.analysis_service import AnalysisService


def get_analysis_service() -> AnalysisService:
    return AnalysisService(
        section_service=get_section_service(),
        uow_factory=_build_uow_factory(),
    )
```

Update `backend-python/app/main.py` imports and router registration:

```python
from app.api import analysis_controller, document_controller, provider_controller, section_controller

app.include_router(document_controller.router, prefix="/api")
app.include_router(section_controller.router, prefix="/api")
app.include_router(provider_controller.router, prefix="/api")
app.include_router(analysis_controller.router, prefix="/api")
```

- [ ] **Step 6: Run backend tests and verify Green for the API slice**

Run: `rtk pytest backend-python/tests/unit/services/test_analysis_service.py backend-python/tests/integration/api/test_analysis_controller.py -q`

Expected: PASS for the new section analysis service and controller tests.

## Task 3: Lock Frontend Generate-and-Display Behavior with Failing Tests

**Files:**
- Modify: `src/features/workspace/components/center/DocumentViewer.test.tsx`
- Modify: `src/features/workspace/pages/WorkspacePage.test.tsx`

- [ ] **Step 1: Add a failing viewer test for the generate-analysis action state**

Append a test like this to `src/features/workspace/components/center/DocumentViewer.test.tsx`:

```tsx
  it("选择章节且无解析时显示生成解析按钮", () => {
    render(
      <DocumentViewer
        contentBlocks={[]}
        selectedSectionId="sec-1"
        viewerStatus="ready"
        footnotes={[]}
        expandedFootnoteId={null}
        showSelectionMenu={false}
        selectionMenuPos={null}
        onUpdateLineText={vi.fn()}
        onToggleFootnote={vi.fn()}
        onShowSelectionMenu={vi.fn()}
        onQuoteSelection={vi.fn()}
        units={[{ id: "u1", sequence_index: 0, page_number: 1, text_content: "原文内容" }]}
        analysisStatus="idle"
        onGenerateAnalysis={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: "生成解析" })).toBeDefined();
  });
```

- [ ] **Step 2: Add a failing workspace test for generate-and-display flow**

In `src/features/workspace/pages/WorkspacePage.test.tsx`, mock the future analysis API and add:

```tsx
  it("章节没有解析时可点击生成，并在成功后展示解析内容", async () => {
    (uploadDocument as Mock).mockResolvedValueOnce({ id: "doc-1" });
    (getDocumentDetail as Mock).mockResolvedValueOnce({
      document: { id: "doc-1", title: "doc-1" },
      units: [{ id: "u1", sequence_index: 0, page_number: 1, text_content: "第一页原文" }],
    });
    (buildSections as Mock).mockResolvedValueOnce([{ id: "sec-1", title: "第一节", level: 1 }]);
    (getSectionTree as Mock).mockResolvedValueOnce([{ id: "sec-1", title: "第一节", level: 1, order_index: 0, children: [] }]);
    (getSectionContent as Mock).mockResolvedValue({
      anchor_unit_id: "u1",
      units: [{ id: "u1", sequence_index: 0, page_number: 1, text_content: "第一页原文" }],
    });
    (getSectionAnalysis as Mock).mockRejectedValueOnce(new Error("请求失败 (404): 该章节暂无解析"));
    (generateSectionAnalysis as Mock).mockResolvedValueOnce({
      id: "analysis-1",
      document_id: "doc-1",
      section_id: "sec-1",
      analysis_type: "section",
      language: "zh",
      content_markdown: "## 中文总结\n\n这是摘要",
      content_json: {
        summary: "这是摘要",
        key_concepts: ["概念 A"],
        terms: [],
        highlights: ["重点 A"],
        source_refs: [{ page: 1, title: "第一节" }],
      },
      source_refs: [{ page: 1, title: "第一节" }],
      created_at: "2026-06-29T12:00:00Z",
      updated_at: "2026-06-29T12:00:00Z",
    });

    render(<WorkspacePage />);
    await uploadPdf("lecture.pdf");

    fireEvent.click(await screen.findByText("第一节"));
    fireEvent.click(await screen.findByRole("button", { name: "生成解析" }));

    expect(await screen.findByText("这是摘要")).toBeDefined();
    expect(screen.getByText("概念 A")).toBeDefined();
  });
```

- [ ] **Step 3: Run focused frontend tests and verify Red**

Run: `rtk npm test -- src/features/workspace/components/center/DocumentViewer.test.tsx src/features/workspace/pages/WorkspacePage.test.tsx --runInBand`

Expected: FAIL because `DocumentViewer` does not yet expose the generate action props and `WorkspacePage` has no analysis query/generate flow.

## Task 4: Implement Frontend Analysis Query, Generate, and Display

**Files:**
- Create: `src/types/analysis.ts`
- Create: `src/features/analysis/api/analysisApi.ts`
- Create: `src/features/analysis/analysisToContentBlocks.ts`
- Modify: `src/features/workspace/type.ts`
- Modify: `src/features/workspace/components/center/DocumentViewer.tsx`
- Modify: `src/features/workspace/pages/WorkspacePage.tsx`

- [ ] **Step 1: Add frontend analysis DTO types**

Create `src/types/analysis.ts`:

```ts
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
```

- [ ] **Step 2: Add frontend analysis API wrappers**

Create `src/features/analysis/api/analysisApi.ts`:

```ts
import { request } from "../../../lib/apiClient";
import type {
  GenerateSectionAnalysisPayload,
  SectionAnalysisResponse,
} from "../../../types/analysis";

export function getSectionAnalysis(sectionId: string): Promise<SectionAnalysisResponse> {
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
```

- [ ] **Step 3: Add a pure mapper from analysis content to viewer blocks**

Create `src/features/analysis/analysisToContentBlocks.ts`:

```ts
import type { SectionAnalysisResponse } from "../../types/analysis";
import type { ContentBlock, ContentLine } from "../../types/section";

function toParagraphLines(prefix: string, values: string[]): ContentLine[] {
  return values.map((value, index) => ({
    id: `${prefix}-${index}`,
    text: value,
    type: "paragraph",
  }));
}

export function analysisToContentBlocks(analysis: SectionAnalysisResponse): ContentBlock[] {
  const content = analysis.content_json;
  if (!content) return [];

  const blocks: ContentBlock[] = [];

  if (content.summary) {
    blocks.push({
      id: `${analysis.section_id}-summary`,
      sectionId: analysis.section_id,
      title: "摘要",
      contentType: "text",
      lines: [{ id: `${analysis.section_id}-summary-line`, text: content.summary, type: "paragraph" }],
    });
  }

  if (content.key_concepts.length > 0) {
    blocks.push({
      id: `${analysis.section_id}-concepts`,
      sectionId: analysis.section_id,
      title: "核心概念",
      contentType: "text",
      lines: toParagraphLines(`${analysis.section_id}-concept`, content.key_concepts),
    });
  }

  if (content.terms.length > 0) {
    blocks.push({
      id: `${analysis.section_id}-terms`,
      sectionId: analysis.section_id,
      title: "中法术语",
      contentType: "text",
      lines: content.terms.map((term, index) => ({
        id: `${analysis.section_id}-term-${index}`,
        text: `${term.fr} / ${term.zh}：${term.explanation}`,
        type: "paragraph",
      })),
    });
  }

  if (content.highlights.length > 0) {
    blocks.push({
      id: `${analysis.section_id}-highlights`,
      sectionId: analysis.section_id,
      title: "重点提炼",
      contentType: "text",
      lines: toParagraphLines(`${analysis.section_id}-highlight`, content.highlights),
    });
  }

  return blocks;
}
```

- [ ] **Step 4: Extend viewer props and show generate/loading/error actions in the parsed panel**

Update `src/features/workspace/type.ts` `DocumentViewerProps`:

```ts
  analysisStatus?: "idle" | "loading" | "ready" | "error";
  analysisErrorMessage?: string | null;
  onGenerateAnalysis?: () => void;
```

Update `src/features/workspace/components/center/DocumentViewer.tsx` so the empty parsed panel can render:

```tsx
            {showEmptyState ? (
              <div className="inline-block pt-16 pl-6">
                <div className="w-16 h-16 rounded-2xl bg-black/5 flex items-center justify-center mb-4">
                  {/* existing icon */}
                </div>
                <p className="text-sm text-neutral-500 font-medium">{emptyStateCopy.title}</p>
                <p className="text-xs text-neutral-400 mt-1">{emptyStateCopy.subtitle}</p>
                {selectedSectionId && hasRawUnits && onGenerateAnalysis && analysisStatus !== "ready" && (
                  <div className="mt-4">
                    <button
                      onClick={onGenerateAnalysis}
                      disabled={analysisStatus === "loading"}
                      className="rounded-lg bg-blue-600 px-3 py-2 text-xs text-white disabled:opacity-60"
                    >
                      {analysisStatus === "loading" ? "生成中..." : "生成解析"}
                    </button>
                    {analysisStatus === "error" && analysisErrorMessage && (
                      <p className="mt-2 text-xs text-rose-500">{analysisErrorMessage}</p>
                    )}
                  </div>
                )}
              </div>
            ) : (
```

- [ ] **Step 5: Add analysis orchestration and per-section caching in `WorkspacePage`**

Update `src/features/workspace/pages/WorkspacePage.tsx` with new state like:

```ts
  const [sectionAnalysisByFileId, setSectionAnalysisByFileId] = useState<Record<string, Record<string, ContentBlock[]>>>({});
  const [sectionAnalysisStatusByFileId, setSectionAnalysisStatusByFileId] = useState<Record<string, Record<string, "idle" | "loading" | "ready" | "error">>>({});
  const [sectionAnalysisErrorByFileId, setSectionAnalysisErrorByFileId] = useState<Record<string, Record<string, string | null>>>({});
```

Add helpers:

```ts
  const loadSectionAnalysis = useCallback(async (fileId: string, sectionId: string) => {
    setSectionAnalysisStatusByFileId((prev) => ({
      ...prev,
      [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: "loading" },
    }));

    try {
      const analysis = await getSectionAnalysis(sectionId);
      const blocks = analysisToContentBlocks(analysis);
      setSectionAnalysisByFileId((prev) => ({
        ...prev,
        [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: blocks },
      }));
      setSectionAnalysisStatusByFileId((prev) => ({
        ...prev,
        [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: "ready" },
      }));
      setSectionAnalysisErrorByFileId((prev) => ({
        ...prev,
        [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: null },
      }));
      dispatch({ type: "SET_LANG_DATA", sections: documentSectionsByFileId[fileId] ?? [], contentBlocks: blocks });
    } catch (err) {
      const message = err instanceof Error ? err.message : "解析加载失败";
      const isMissing = message.includes("404");
      setSectionAnalysisStatusByFileId((prev) => ({
        ...prev,
        [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: isMissing ? "idle" : "error" },
      }));
      setSectionAnalysisErrorByFileId((prev) => ({
        ...prev,
        [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: isMissing ? null : message },
      }));
      dispatch({ type: "SET_LANG_DATA", sections: documentSectionsByFileId[fileId] ?? [], contentBlocks: [] });
    }
  }, [documentSectionsByFileId]);
```

And generation:

```ts
  const handleGenerateAnalysis = useCallback(async () => {
    if (!selectedFileId || !state.selectedSectionId) return;
    const fileId = selectedFileId;
    const sectionId = state.selectedSectionId;

    setSectionAnalysisStatusByFileId((prev) => ({
      ...prev,
      [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: "loading" },
    }));
    setSectionAnalysisErrorByFileId((prev) => ({
      ...prev,
      [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: null },
    }));

    try {
      const analysis = await generateSectionAnalysis(sectionId);
      const blocks = analysisToContentBlocks(analysis);
      setSectionAnalysisByFileId((prev) => ({
        ...prev,
        [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: blocks },
      }));
      setSectionAnalysisStatusByFileId((prev) => ({
        ...prev,
        [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: "ready" },
      }));
      dispatch({ type: "SET_LANG_DATA", sections: documentSectionsByFileId[fileId] ?? [], contentBlocks: blocks });
    } catch (err) {
      const message = err instanceof Error ? err.message : "生成解析失败";
      setSectionAnalysisStatusByFileId((prev) => ({
        ...prev,
        [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: "error" },
      }));
      setSectionAnalysisErrorByFileId((prev) => ({
        ...prev,
        [fileId]: { ...(prev[fileId] ?? {}), [sectionId]: message },
      }));
    }
  }, [documentSectionsByFileId, selectedFileId, state.selectedSectionId]);
```

Call `loadSectionAnalysis(fileId, sectionId)` whenever section raw content is loaded successfully.

- [ ] **Step 6: Run focused frontend tests and verify Green**

Run: `rtk npm test -- src/features/workspace/components/center/DocumentViewer.test.tsx src/features/workspace/pages/WorkspacePage.test.tsx --runInBand`

Expected: PASS for generate button visibility, generation success rendering, and failure/retry states.

## Task 5: Add Analysis Persistence and Reuse

**Files:**
- Modify: `backend-python/app/repositories/analysis_result_repository.py`
- Modify: `backend-python/app/api/dependencies.py`
- Modify: `backend-python/app/services/analysis_service.py`
- Modify: `backend-python/tests/unit/services/test_analysis_service.py`
- Modify: `backend-python/tests/integration/api/test_analysis_controller.py`
- Modify: `backend-python/tests/integration/persistence/test_sqlite_repositories.py`

- [ ] **Step 1: Add a failing repository integration test for section lookup**

Append to `backend-python/tests/integration/persistence/test_sqlite_repositories.py`:

```python
def test_analysis_result_repository_get_by_section_id(session):
    from app.entities.analysis_result import AnalysisResult
    from app.enums.analysis_type import AnalysisType
    from app.repositories.analysis_result_repository import AnalysisResultRepository

    repo = AnalysisResultRepository(session)
    saved = AnalysisResult(
        document_id="doc-1",
        section_id="sec-1",
        analysis_type=AnalysisType.SECTION,
        language="zh",
        content_markdown="## 中文总结\n\n摘要",
        content_json={"summary": "摘要", "key_concepts": [], "terms": [], "highlights": [], "source_refs": []},
    )
    repo.save(saved)
    session.commit()

    loaded = repo.get_by_section_id("sec-1")

    assert loaded is not None
    assert loaded.section_id == "sec-1"
```

- [ ] **Step 2: Extend the repository with section-level lookup**

Add to `backend-python/app/repositories/analysis_result_repository.py`:

```python
    def get_by_section_id(self, section_id: str) -> AnalysisResult | None:
        model = (
            self.session.query(AnalysisResultModel)
            .filter(AnalysisResultModel.section_id == section_id)
            .one_or_none()
        )
        if model is None:
            return None
        return self._to_entity(model)

    def _to_entity(self, model: AnalysisResultModel) -> AnalysisResult:
        return AnalysisResult(
            id=model.id,
            document_id=model.document_id,
            section_id=model.section_id,
            analysis_type=model.analysis_type,
            language=model.language,
            content_markdown=model.content_markdown,
            content_json=json_object(model.content_json),
            model_name=model.model_name,
            prompt_version=model.prompt_version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
```

Then make `get_by_id()` delegate to `_to_entity()`.

- [ ] **Step 3: Wire repository-backed reuse and save into `AnalysisService`**

Update `backend-python/app/api/dependencies.py` so the service gets the repository through a UOW-backed closure:

```python
def get_analysis_service() -> AnalysisService:
    return AnalysisService(
        section_service=get_section_service(),
        uow_factory=_build_uow_factory(),
    )
```

Update `backend-python/app/services/analysis_service.py` generation flow:

```python
    def get_section_analysis(self, section_id: str):
        if self.uow_factory is None:
            return None
        from app.repositories.analysis_result_repository import AnalysisResultRepository

        with self.uow_factory() as uow:
            return AnalysisResultRepository(uow.session).get_by_section_id(section_id)

    async def generate_section_analysis(...):
        if not force_regenerate:
            existing = self.get_section_analysis(section_id)
            if existing is not None:
                return existing

        ...

        result = AnalysisResult(...)

        if self.uow_factory is not None:
            from app.repositories.analysis_result_repository import AnalysisResultRepository

            with self.uow_factory() as uow:
                AnalysisResultRepository(uow.session).save(result)
                uow.commit()

        return result
```

- [ ] **Step 4: Extend service and API tests for reuse without regeneration**

Add to `backend-python/tests/unit/services/test_analysis_service.py`:

```python
@pytest.mark.asyncio
async def test_generate_section_analysis_reuses_existing_result_when_not_forced():
    existing = AnalysisResult(
        document_id="doc-1",
        section_id="sec-1",
        analysis_type=AnalysisType.SECTION,
        language="zh",
        content_markdown="## 中文总结\n\n已存在摘要",
        content_json={"summary": "已存在摘要", "key_concepts": [], "terms": [], "highlights": [], "source_refs": []},
    )
    service = AnalysisService(
        section_service=MagicMock(),
        analysis_agent=MagicMock(),
        analysis_result_repository=MagicMock(),
        uow_factory=None,
    )
    service.get_section_analysis = MagicMock(return_value=existing)

    result = await service.generate_section_analysis("sec-1", force_regenerate=False)

    assert result.content_json["summary"] == "已存在摘要"
```

Extend `backend-python/tests/integration/api/test_analysis_controller.py`:

```python
def test_get_section_analysis_success(client):
    test_client, analysis_service = client
    from app.entities.analysis_result import AnalysisResult
    from app.enums.analysis_type import AnalysisType

    analysis_service.get_section_analysis.return_value = AnalysisResult(
        document_id="doc-1",
        section_id="sec-1",
        analysis_type=AnalysisType.SECTION,
        language="zh",
        content_markdown="## 中文总结\n\n已存在摘要",
        content_json={"summary": "已存在摘要", "key_concepts": [], "terms": [], "highlights": [], "source_refs": []},
    )

    response = test_client.get("/api/analyses/sections/sec-1")

    assert response.status_code == 200
    assert response.json()["data"]["content_json"]["summary"] == "已存在摘要"
```

- [ ] **Step 5: Run the persistence-focused backend tests and verify Green**

Run: `rtk pytest backend-python/tests/unit/services/test_analysis_service.py backend-python/tests/integration/api/test_analysis_controller.py backend-python/tests/integration/persistence/test_sqlite_repositories.py -q`

Expected: PASS, including section-level save and reload behavior.

## Task 6: Final Focused Verification

**Files:**
- No code changes

- [ ] **Step 1: Run the backend analysis-focused verification suite**

Run: `rtk pytest backend-python/tests/unit/services/test_analysis_service.py backend-python/tests/integration/api/test_analysis_controller.py backend-python/tests/integration/persistence/test_sqlite_repositories.py -q`

Expected: PASS.

- [ ] **Step 2: Run the frontend workspace/viewer verification suite**

Run: `rtk npm test -- src/features/workspace/components/center/DocumentViewer.test.tsx src/features/workspace/pages/WorkspacePage.test.tsx --runInBand`

Expected: PASS.

- [ ] **Step 3: Inspect the final diff before handoff**

Run: `rtk git diff --stat`

Expected: Diff is limited to analysis backend/frontend files, tests, and the two new docs.
