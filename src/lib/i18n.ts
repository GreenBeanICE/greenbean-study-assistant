// 用于中法双语翻译的上下文和工具函数，提供统一的接口获取当前语言和对应的翻译文本

import { createContext, useContext } from "react";

export type Lang = "zh" | "fr";

// 翻译键定义 - 所有键在两个语言中必须一致
const TRANSLATION_KEYS = [
  // Navbar
  "navFeatures", "navScreenshots", "navWorkflow", "langToggle", "login",
  // Hero
  "heroBadge", "heroTitle1", "heroTitle2", "heroDesc",
  "heroCta", "heroLearnMore", "heroImagePlaceholder",
  // Features
  "featuresTitle", "featuresTitleSuffix", "featuresDesc",
  "feature1Title", "feature1Desc", "feature2Title", "feature2Desc",
  "feature3Title", "feature3Desc", "feature4Title", "feature4Desc",
  // Screenshots
  "screenshotsTitle", "screenshotsDesc",
  "screenshot1Label", "screenshot1Desc",
  "screenshot2Label", "screenshot2Desc",
  "screenshot3Label", "screenshot3Desc",
  "screenshot4Label", "screenshot4Desc",
  "screenshot5Label", "screenshot5Desc",
  "screenshotPlaceholder",
  // Workflow
  "workflowTitle", "workflowDesc",
  "step1Title", "step1Desc", "step2Title", "step2Desc",
  "step3Title", "step3Desc", "stepLabel",
  // UploadZone
  "uploadPrompt", "uploadFormat",
  "formatDoc", "formatWord", "formatPpt", "formatText", "formatOcr",
  // Login Modal
  "loginTitle", "loginDesc", "loginContinue", "loginLater",
  // Bottom CTA
  "ctaTitle", "ctaDesc", "ctaButton",
  // Footer
  "footerAbout", "footerPrivacy", "footerTerms",
] as const;

// 将键值对数组转为带有字面量类型的 Record
function buildTranslations<T extends readonly (readonly [string, string])[]>(
  entries: T,
): { [K in T[number] as K[0]]: K[1] } {
  const result = {} as { [K in T[number] as K[0]]: K[1] };
  for (const [key, value] of entries) {
    (result as Record<string, string>)[key] = value;
  }
  return result;
}

// 中文翻译值
const zhValues: readonly (readonly [string, string])[] = [
  // Navbar
  ["navFeatures", "功能特性"],
  ["navScreenshots", "使用体验"],
  ["navWorkflow", "解析流程"],
  ["langToggle", "FR / 中文"],
  ["login", "登录"],
  // Hero
  ["heroBadge", "面向在法中国留学生"],
  ["heroTitle1", "让法国课程"],
  ["heroTitle2", "不再难懂"],
  ["heroDesc", "GreenBean 帮助你将法语课件自动解析、整理知识结构，并提供 AI 深度分析。专注学习本身，语言和整理交给我们。"],
  ["heroCta", "开始使用"],
  ["heroLearnMore", "了解更多"],
  ["heroImagePlaceholder", "产品截图占位"],
  // Features
  ["featuresTitle", "为什么选择"],
  ["featuresTitleSuffix", "？"],
  ["featuresDesc", "专为在法中国留学生设计，打通从课件导入到深度理解的完整链路。"],
  ["feature1Title", "课件智能解析"],
  ["feature1Desc", "支持 PDF、PPT、Word、图片，自动提取文字与结构，生成清晰的课程大纲。"],
  ["feature2Title", "AI 深度分析"],
  ["feature2Desc", "基于课程内容自动生成总结、重点提炼、术语解释，让复习事半功倍。"],
  ["feature3Title", "知识结构化"],
  ["feature3Desc", "自动将课件拆分为章节、知识点，构建体系化的学习知识树。"],
  ["feature4Title", "智能问答"],
  ["feature4Desc", "针对课程内容自由提问，AI 结合上下文给出精准回答，像私教一样陪学。"],
  // Screenshots
  ["screenshotsTitle", "真实使用体验"],
  ["screenshotsDesc", "以下是在 GreenBean 中的实际操作界面预览。"],
  ["screenshot1Label", "课程概览"],
  ["screenshot1Desc", "一目了然的知识结构"],
  ["screenshot2Label", "AI 问答"],
  ["screenshot2Desc", "深度对话理解"],
  ["screenshot3Label", "解析报告"],
  ["screenshot3Desc", "自动生成的复习摘要"],
  ["screenshot4Label", "文件管理"],
  ["screenshot4Desc", "统一管理所有课件"],
  ["screenshot5Label", "章节导航"],
  ["screenshot5Desc", "快速定位知识点"],
  ["screenshotPlaceholder", "截图待添加"],
  // Workflow
  ["workflowTitle", "三步搞定课程解析"],
  ["workflowDesc", "从上传到理解，只需简单的三个步骤。"],
  ["step1Title", "上传文件"],
  ["step1Desc", "拖拽或选择你的法语课件，支持 PDF / PPT / Word / 图片等多种格式。"],
  ["step2Title", "自动解析"],
  ["step2Desc", "AI 自动提取文字内容，识别章节结构，生成知识索引树。"],
  ["step3Title", "深度互动"],
  ["step3Desc", "基于课程内容提问、生成测验、梳理重点，真正做到学透。"],
  ["stepLabel", "步骤"],
  // UploadZone
  ["uploadPrompt", "拖拽文件到此处，或点击上传"],
  ["uploadFormat", "支持 PDF、DOCX、PPTX、TXT、MD、JPG、PNG、WEBP 格式"],
  ["formatDoc", "文档"],
  ["formatWord", "Word"],
  ["formatPpt", "PowerPoint"],
  ["formatText", "纯文本"],
  ["formatOcr", "图片 OCR"],
  // Login Modal
  ["loginTitle", "登录以使用上传功能"],
  ["loginDesc", "请先登录你的账户，即可上传课件并享受完整的 AI 解析服务。"],
  ["loginContinue", "继续登录"],
  ["loginLater", "稍后再说"],
  // Bottom CTA
  ["ctaTitle", "准备好提升学习效率了吗？"],
  ["ctaDesc", "免费开始使用 GreenBean，让法国课程学习变得更轻松、更高效。"],
  ["ctaButton", "免费开始使用"],
  // Footer
  ["footerAbout", "关于我们"],
  ["footerPrivacy", "隐私政策"],
  ["footerTerms", "使用条款"],
];

// 法语翻译值
const frValues: readonly (readonly [string, string])[] = [
  // Navbar
  ["navFeatures", "Fonctionnalités"],
  ["navScreenshots", "Aperçus"],
  ["navWorkflow", "Processus"],
  ["langToggle", "FR / 中文"],
  ["login", "Connexion"],
  // Hero
  ["heroBadge", "Assistant IA pour étudiants chinois en France"],
  ["heroTitle1", "Les cours français"],
  ["heroTitle2", "enfin accessibles"],
  ["heroDesc", "GreenBean analyse automatiquement vos cours en français, organise les connaissances et fournit une analyse IA approfondie. Concentrez-vous sur l'apprentissage, laissez-nous gérer le reste."],
  ["heroCta", "Commencer"],
  ["heroLearnMore", "En savoir plus"],
  ["heroImagePlaceholder", "Placeholder capture"],
  // Features
  ["featuresTitle", "Pourquoi choisir"],
  ["featuresTitleSuffix", " ?"],
  ["featuresDesc", "Conçu pour les étudiants chinois en France, du cours à la compréhension approfondie."],
  ["feature1Title", "Analyse intelligente"],
  ["feature1Desc", "PDF, PPT, Word, images : extraction automatique du texte et génération d'un plan de cours clair."],
  ["feature2Title", "Analyse IA"],
  ["feature2Desc", "Résumés automatiques, points clés, explications terminologiques pour des révisions efficaces."],
  ["feature3Title", "Structuration"],
  ["feature3Desc", "Découpage automatique en chapitres et notions pour construire un arbre de connaissances."],
  ["feature4Title", "Q&A intelligent"],
  ["feature4Desc", "Posez des questions librement, l'IA répond avec précision en contexte. Comme un tuteur personnel."],
  // Screenshots
  ["screenshotsTitle", "Expérience utilisateur"],
  ["screenshotsDesc", "Aperçu des interfaces GreenBean en action."],
  ["screenshot1Label", "Vue d'ensemble"],
  ["screenshot1Desc", "Structure claire des connaissances"],
  ["screenshot2Label", "Q&A IA"],
  ["screenshot2Desc", "Dialogue approfondi"],
  ["screenshot3Label", "Rapport d'analyse"],
  ["screenshot3Desc", "Résumé de révision automatique"],
  ["screenshot4Label", "Gestion fichiers"],
  ["screenshot4Desc", "Tous vos cours centralisés"],
  ["screenshot5Label", "Navigation chapitres"],
  ["screenshot5Desc", "Accès rapide aux notions"],
  ["screenshotPlaceholder", "Capture à venir"],
  // Workflow
  ["workflowTitle", "3 étapes pour analyser vos cours"],
  ["workflowDesc", "De l'import à la compréhension, en trois étapes simples."],
  ["step1Title", "Importer"],
  ["step1Desc", "Glissez-déposez ou sélectionnez vos cours (PDF, PPT, Word, images)."],
  ["step2Title", "Analyser"],
  ["step2Desc", "L'IA extrait le texte, identifie les chapitres et génère un index."],
  ["step3Title", "Interagir"],
  ["step3Desc", "Posez des questions, générez des quiz, maîtrisez vraiment la matière."],
  ["stepLabel", "Étape"],
  // UploadZone
  ["uploadPrompt", "Glissez-déposez ou cliquez pour importer"],
  ["uploadFormat", "Formats supportés : PDF, DOCX, PPTX, TXT, MD, JPG, PNG, WEBP"],
  ["formatDoc", "Document"],
  ["formatWord", "Word"],
  ["formatPpt", "PowerPoint"],
  ["formatText", "Texte"],
  ["formatOcr", "Image OCR"],
  // Login Modal
  ["loginTitle", "Connectez-vous pour importer"],
  ["loginDesc", "Connectez-vous pour importer vos cours et profiter de l'analyse IA complète."],
  ["loginContinue", "Continuer"],
  ["loginLater", "Plus tard"],
  // Bottom CTA
  ["ctaTitle", "Prêt à booster votre apprentissage ?"],
  ["ctaDesc", "Commencez gratuitement avec GreenBean et simplifiez vos études en français."],
  ["ctaButton", "Commencer gratuitement"],
  // Footer
  ["footerAbout", "À propos"],
  ["footerPrivacy", "Confidentialité"],
  ["footerTerms", "Conditions"],
];

// 通过 buildTranslations 构建 Record，zh 和 fr 各自独立、无结构重复
const zh = buildTranslations(zhValues) as Record<string, string>;
const fr = buildTranslations(frValues) as Record<string, string>;

export const translations = { zh, fr } as const;

export type TranslationKeys = keyof typeof translations.zh;

export interface I18nContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: TranslationKeys) => string;
}

export const I18nContext = createContext<I18nContextValue>({
  lang: "zh",
  setLang: () => {},
  t: (key) => translations.zh[key],
});

export function useI18n() {
  return useContext(I18nContext);
}