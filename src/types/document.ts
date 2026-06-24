/**
 * 文档相关全局 TypeScript 类型。
 *
 * 与后端 app/schemas/document_schema.py 的响应结构对齐，
 * 前端只消费这些经过裁剪的视图，不直接使用 Entity 原始结构。
 */

/** 后端解析出的文档单元（对应 DocumentUnitSummary） */
export interface DocumentUnit {
  id: string;
  sequence_index: number;
  page_number: number | null;
  text_content: string;
}

/** 文档摘要（对应 DocumentListItem / DocumentUploadResponse） */
export interface DocumentSummary {
  id: string;
  workspace_id: string;
  title: string;
  original_filename: string;
  file_type: string;
  status: string;
  page_count: number | null;
  created_at: string;
}

/** 文档详情（含 units 列表） */
export interface DocumentDetail {
  document: DocumentSummary;
  units: DocumentUnit[];
}

/** 上传接口响应 */
export interface DocumentUploadResponse {
  id: string;
  title: string;
  original_filename: string;
  file_type: string;
  status: string;
  page_count: number | null;
  created_at: string;
}
