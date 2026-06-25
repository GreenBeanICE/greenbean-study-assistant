import type {
  SectionNode,
  ContentBlock,
  FootnoteReference,
  SourceCitation,
  SourcePage,
  TextSelection,
} from "../../types/section";
import type { ChatMessage } from "../../types/chat";

export type TextFormatAction = "bold" | "italic" | "underline" | "strikethrough" | "highlight" | "align-left" | "align-center" | "align-right" | "align-justify" | "insert-image" | "insert-table";

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
  rightPanelMode: "chat" | "sources";
  sourcePages: SourcePage[];
  activeSourceCitations: SourceCitation[];
  tokenUsage: number;
  leftCollapsed: boolean;
  rightCollapsed: boolean;
  leftPanelWidth: number;
  rightPanelWidth: number;
  documentTitle: string;
}

export type WorkspaceAction =
  | { type: "SELECT_SECTION"; sectionId: string }
  | { type: "TOGGLE_SECTION_EXPAND"; sectionId: string }
  | { type: "TOGGLE_HIGHLIGHT"; blockId: string; lineId: string }
  | { type: "UPDATE_LINE_TEXT"; blockId: string; lineId: string; text: string }
  | { type: "FORMAT_LINE"; blockId: string; lineId: string; format: TextFormatAction }
  | { type: "TOGGLE_FOOTNOTE"; footnoteId: string }
  | { type: "SET_SELECTION"; selection: TextSelection | null }
  | { type: "SHOW_SELECTION_MENU"; show: boolean; pos?: { x: number; y: number } }
  | { type: "QUOTE_SELECTION" }
  | { type: "CLEAR_QUOTE" }
  | { type: "SHOW_SOURCES"; citations: SourceCitation[] }
  | { type: "SHOW_CHAT" }
  | { type: "SET_CHAT_INPUT"; text: string }
  | { type: "SEND_CHAT_MESSAGE"; message: ChatMessage }
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
  footnotes: FootnoteReference[];
  expandedFootnoteId: string | null;
  currentSelection: TextSelection | null;
  showSelectionMenu: boolean;
  selectionMenuPos: { x: number; y: number } | null;
  onToggleHighlight: (blockId: string, lineId: string) => void;
  onUpdateLineText: (blockId: string, lineId: string, text: string) => void;
  onFormatLine: (blockId: string, lineId: string, format: TextFormatAction) => void;
  onToggleFootnote: (footnoteId: string) => void;
  onSelectText: (selection: TextSelection | null) => void;
  onShowSelectionMenu: (show: boolean, pos?: { x: number; y: number }) => void;
  onQuoteSelection: () => void;
  onShowSources: (citations: SourceCitation[]) => void;
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

export interface WorkspacePageProps {
  /** 工作区唯一标识（可选，后续可根据此加载不同数据） */
  workspaceId?: string;
}
