/**
 * 章节 API 封装 —— 对 apiClient 的薄封装。
 *
 * 所有函数通过相对路径 /api/sections/... 访问后端，
 * 开发期由 vite proxy 转发（见 vite.config.ts server.proxy），
 * 生产环境需由部署层或 Tauri 桥接处理路由。
 */
import { request } from "../../../lib/apiClient";
import type { SectionNode } from "../../../types/section";

/** 后端返回的章节树节点结构 */
interface SectionTreeNodeResponse {
  id: string;
  title: string;
  level: number;
  order_index: number;
  children: SectionTreeNodeResponse[];
}

/**
 * 将后端的 SectionTreeNodeResponse 递归转换为前端的 SectionNode。
 * - `order_index` 转为 `index` 字符串（如 "1.2"）
 * - 默认 `expanded: true`
 */
function toSectionNode(
  node: SectionTreeNodeResponse,
  parentIndex?: string,
): SectionNode {
  const index = parentIndex
    ? `${parentIndex}.${node.order_index + 1}`
    : `${node.order_index + 1}`;

  return {
    id: node.id,
    title: node.title,
    index,
    expanded: true,
    children: node.children?.map((child) => toSectionNode(child, index)),
  };
}

/**
 * 触发后端为指定文档构建章节树。
 * 如果章节树已存在，后端会直接返回已有数据。
 * @returns 章节列表（扁平结构）
 */
export async function buildSections(
  documentId: string,
): Promise<{ id: string; title: string; level: number }[]> {
  return request(`/sections/documents/${documentId}/build`);
}

/**
 * 获取指定文档的章节树。
 * @returns 树形结构的 SectionNode 数组
 */
export async function getSectionTree(
  documentId: string,
): Promise<SectionNode[]> {
  const nodes = await request<SectionTreeNodeResponse[]>(
    `/sections/documents/${documentId}/tree`,
  );
  return nodes.map((node) => toSectionNode(node));
}
