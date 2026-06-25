export type Purpose = "chat" | "embedding";
export type ApiMode = "openai-compat";

/** Provider 配置（列表/详情响应，后端已脱敏，不含 api_key）。 */
export interface ProviderConfig {
  id: string;
  name: string;
  api_mode: ApiMode;
  api_host: string;
  api_path: string;
  model_id: string;
  display_name: string;
  context_window: number;
  max_output_tokens: number;
  purpose: Purpose;
  embedding_dimension: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** 新增 / 编辑表单提交载荷。 */
export interface ProviderPayload {
  name: string;
  api_mode: ApiMode;
  api_key: string;
  api_host: string;
  api_path?: string;
  model_id: string;
  display_name: string;
  context_window?: number;
  max_output_tokens?: number;
  purpose: Purpose;
  embedding_dimension?: number | null;
}

/** 激活 / 当前激活响应。 */
export interface ActivateResponse {
  id: string;
  name: string;
  display_name: string;
  model_id: string;
}
