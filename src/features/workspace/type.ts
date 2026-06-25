import type { SectionNode, ContentBlock, FootnoteReference, TextSelection } from "../../types/section";
import type { ChatMessage } from "../../types/chat";
import type { DocumentUnit } from "../../types/document";

export type TextFormatAction = "bold" | "italic" | "underline" | "strikethrough" | "highlight" | "align-left" | "align-center" | "align-right" | "align-justify" | "insert-image" | "insert-table";

export type FileType = "PDF" | "DOC" | "PPT" | "IMG" | "TXT" | "MD";
export type FileStatus = "parsed" | "parsing" | "pending";
export type ViewerStatus = "idle" | "parsing" | "ready" | "empty" | "error";

export interface FileItem {
  id: string;
  name: string;
  type: FileType;
  category: string;
  size: string;
  date: string;
  status: FileStatus;
  documentId?: string;
  viewerStatus?: ViewerStatus;
}

export interface Folder {
  key: string;
  label: string;
}

export interface WorkspaceState {
  sections: SectionNode[];
  selectedSectionId: string | null;
  contentBlocks: ContentBlock[];
  chatMessages: ChatMessage[];
  chatInput: string;
  loading: boolean;
  footnotes: FootnoteReference[];
  expandedFootnoteId: string | null;
  currentSelection: TextSelection | null;
  showSelectionMenu: boolean;
  selectionMenuPos: { x: number; y: number } | null;
  quotedText: string | null;
  tokenUsage: number;
  leftCollapsed: boolean;
  rightCollapsed: boolean;
  leftPanelWidth: number;
  rightPanelWidth: number;
  documentTitle: string;
}

export type WorkspaceAction =
  | { type: "SELECT_SECTION"; sectionId: string | null }
  | { type: "TOGGLE_SECTION_EXPAND"; sectionId: string }
  | { type: "TOGGLE_HIGHLIGHT"; blockId: string; lineId: string }
  | { type: "UPDATE_LINE_TEXT"; blockId: string; lineId: string; text: string }
  | { type: "FORMAT_LINE"; blockId: string; lineId: string; format: TextFormatAction }
  | { type: "TOGGLE_FOOTNOTE"; footnoteId: string }
  | { type: "SET_SELECTION"; selection: TextSelection | null }
  | { type: "SHOW_SELECTION_MENU"; show: boolean; pos?: { x: number; y: number } }
  | { type: "QUOTE_SELECTION" }
  | { type: "CLEAR_QUOTE" }
  | { type: "SET_CHAT_INPUT"; text: string }
  | { type: "SEND_CHAT_MESSAGE" }
  | { type: "SET_LOADING"; loading: boolean }
  | { type: "SET_TOKEN_USAGE"; usage: number }
  | { type: "TOGGLE_LEFT_PANEL" }
  | { type: "TOGGLE_RIGHT_PANEL" }
  | { type: "SET_LEFT_WIDTH"; width: number }
  | { type: "SET_RIGHT_WIDTH"; width: number }
  | { type: "SET_LANG_DATA"; sections: SectionNode[]; contentBlocks: ContentBlock[] }
  | { type: "SET_DOC_TITLE"; title: string };

export interface SectionTreeProps {
  sections: SectionNode[];
  selectedSectionId: string | null;
  onSelect: (sectionId: string) => void;
  onToggle: (sectionId: string) => void;
}

export interface DocumentViewerProps {
  contentBlocks: ContentBlock[];
  selectedSectionId: string | null;
  viewerStatus?: ViewerStatus;
  pendingFileName?: string;
  errorMessage?: string | null;
  footnotes: FootnoteReference[];
  expandedFootnoteId: string | null;
  showSelectionMenu: boolean;
  selectionMenuPos: { x: number; y: number } | null;
  onUpdateLineText: (blockId: string, lineId: string, text: string) => void;
  onToggleFootnote: (footnoteId: string) => void;
  onShowSelectionMenu: (show: boolean, pos?: { x: number; y: number }) => void;
  onQuoteSelection: () => void;
  // 新增：原文面板相关 props
  units?: DocumentUnit[];
  showRawPanel?: boolean;
  showParsedPanel?: boolean;
  onToggleRawPanel?: () => void;
  onToggleParsedPanel?: () => void;
}

export interface ChatPanelProps {
  messages: ChatMessage[];
  input: string;
  quotedText: string | null;
  tokenUsage: number;
  onInputChange: (text: string) => void;
  onSend: () => void;
  onClearQuote: () => void;
  loading: boolean;
}

export interface FileManagerProps {
  files?: FileItem[];
  folders?: Folder[];
  selectedFileId?: string | null;
  onUpload?: (file: File) => void;
  onFileSelect?: (fileId: string) => void;
  onFileSelectWithName?: (fileId: string, fileName: string) => void;
  onDeleteFile?: (fileId: string) => void;
  onRenameFile?: (fileId: string, newName: string) => void;
  onMoveFile?: (fileId: string, toCategory: string) => void;
}

export interface WorkspacePageProps {
  /** 工作区唯一标识（可选，后续可以根据此加载不同数据） */
  workspaceId?: string;
  initialFiles?: FileItem[];
  initialFolders?: Folder[];
  initialSections?: SectionNode[];
  initialContentBlocks?: ContentBlock[];
  initialFootnotes?: FootnoteReference[];
  /** 打开模型设置页（由 App 层注入）。 */
  onOpenSettings?: () => void;
}
