/**
 * 首页宣传截图 SVG 插图集
 */

import React from "react";

export const HeroIllustration: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 480 360" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <defs>
      <linearGradient id="hc" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="white" /><stop offset="100%" stopColor="#fafafa" /></linearGradient>
      <linearGradient id="hbl" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stopColor="#3b82f6" /><stop offset="100%" stopColor="#6366f1" /></linearGradient>
      <filter id="s1"><feDropShadow dx="0" dy="4" stdDeviation="12" floodColor="#0000001A" /></filter>
      <filter id="s2"><feDropShadow dx="0" dy="8" stdDeviation="24" floodColor="#00000012" /></filter>
    </defs>
    <circle cx="240" cy="180" r="160" fill="#f0f0f5" />
    <circle cx="240" cy="180" r="140" fill="white" opacity="0.6" />
    <circle cx="240" cy="180" r="120" stroke="#e5e5ef" strokeWidth="1" strokeDasharray="4 6" />
    <g filter="url(#s1)">
      <rect x="60" y="110" width="160" height="140" fill="url(#hc)" stroke="#eee" strokeWidth="0.5" />
      <rect x="72" y="122" width="28" height="28" fill="url(#hbl)" />
      <circle cx="82" cy="134" r="4" fill="white" opacity="0.4" />
      <circle cx="90" cy="134" r="3" fill="white" opacity="0.2" />
      <rect x="106" y="124" width="90" height="8" fill="#f0f0f0" />
      <rect x="106" y="138" width="70" height="8" fill="#f0f0f0" />
      <rect x="72" y="160" width="130" height="8" fill="#e8e8f0" />
      <rect x="72" y="174" width="100" height="8" fill="#e8e8f0" />
      <rect x="72" y="192" width="50" height="16" fill="#eef2ff" />
      <rect x="128" y="192" width="40" height="16" fill="#fef3c7" />
      <rect x="72" y="214" width="80" height="8" fill="#f0f0f0" />
      <circle cx="72" cy="237" r="3" fill="#22c55e" />
      <text x="80" y="240" fontSize="7" fill="#aaa">已连接 AI 服务</text>
    </g>
    <g filter="url(#s1)">
      <rect x="260" y="100" width="160" height="160" fill="url(#hc)" stroke="#eee" strokeWidth="0.5" />
      <rect x="272" y="112" width="136" height="6" fill="#f0f0f0" />
      <rect x="272" y="124" width="100" height="6" fill="#f0f0f0" />
      <rect x="272" y="142" width="16" height="16" fill="#fef3c7" />
      <rect x="294" y="146" width="80" height="6" fill="#e0e0e0" />
      <rect x="272" y="164" width="100" height="6" fill="#f0f0f0" />
      <rect x="272" y="176" width="120" height="6" fill="#f0f0f0" />
      <rect x="272" y="192" width="136" height="14" fill="#f8f8ff" />
      <rect x="272" y="192" width="40" height="14" fill="#eef2ff" />
      <rect x="316" y="196" width="24" height="6" fill="#c7d2fe" />
      <rect x="348" y="196" width="24" height="6" fill="#c7d2fe" />
      <rect x="380" y="196" width="24" height="6" fill="#c7d2fe" />
      <rect x="272" y="210" width="136" height="14" fill="#f8f8ff" />
      <rect x="316" y="214" width="24" height="6" fill="#e0e0e0" />
      <rect x="348" y="214" width="24" height="6" fill="#e0e0e0" />
      <rect x="380" y="214" width="24" height="6" fill="#e0e0e0" />
      <rect x="272" y="232" width="100" height="6" fill="#fef3c7" />
      <rect x="272" y="244" width="80" height="6" fill="#f0f0f0" />
      <rect x="340" y="246" width="36" height="10" fill="#f0f0f0" />
      <circle cx="350" cy="251" r="2" fill="#000" />
      <circle cx="358" cy="251" r="2" fill="#ccc" />
      <circle cx="366" cy="251" r="2" fill="#ccc" />
    </g>
    <g filter="url(#s2)">
      <rect x="140" y="240" width="200" height="40" fill="white" stroke="#f0f0f0" strokeWidth="0.5" />
      <rect x="152" y="250" width="20" height="20" fill="#fee2e2" />
      <text x="156" y="263" fontSize="6" fontWeight="700" fill="#dc2626">PDF</text>
      <text x="178" y="260" fontSize="7" fontWeight="500" fill="#444">cours-analyse-s1.pdf</text>
      <text x="290" y="260" fontSize="6" fill="#aaa">12.4 MB</text>
      <rect x="152" y="278" width="80" height="14" fill="#f0f0f0" />
      <circle cx="160" cy="285" r="3" fill="#22c55e" />
      <text x="168" y="288" fontSize="6" fill="#666">AI 分析完成</text>
    </g>
    <line x1="220" y1="180" x2="260" y2="180" stroke="#d0d0e0" strokeWidth="1" strokeDasharray="3 3" />
    <circle cx="120" cy="90" r="3" fill="#8b5cf6" opacity="0.3" />
    <circle cx="360" cy="82" r="4" fill="#3b82f6" opacity="0.2" />
    <circle cx="370" cy="270" r="2" fill="#10b981" opacity="0.4" />
    <circle cx="100" cy="260" r="2" fill="#f59e0b" opacity="0.3" />
  </svg>
);

/* ---- 1. 课程概览 ---- */
export const ScreenshotOverview: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 420 260" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <rect x="0" y="0" width="420" height="32" fill="#f8f8f8" />
    <rect x="0" y="16" width="420" height="16" fill="#f8f8f8" />
    <rect x="0" y="32" width="420" height="1" fill="#eee" />
    <circle cx="16" cy="16" r="5" fill="#e5e5e5" />
    <text x="28" y="20" fontSize="10" fontWeight="600" fill="#888">GreenBean</text>
    <rect x="320" y="8" width="24" height="16" fill="#eee" />
    <text x="327" y="19" fontSize="6" fontWeight="500" fill="#666">FR</text>
    <rect x="348" y="8" width="24" height="16" fill="#eee" />
    <circle cx="360" cy="16" r="4" fill="#888" />
    <rect x="376" y="8" width="36" height="16" fill="#000" />
    <text x="385" y="19" fontSize="6" fontWeight="600" fill="white">管理</text>
    <rect x="0" y="33" width="120" height="227" fill="#fafafa" />
    <text x="12" y="49" fontSize="9" fontWeight="600" fill="#666">章节导航</text>
    <text x="100" y="49" fontSize="7" fill="#aaa">5 个章节</text>
    <rect x="6" y="55" width="108" height="22" fill="#000" />
    <text x="14" y="69" fontSize="8" fontWeight="600" fill="#fff">第一章：引言</text>
    <circle cx="20" cy="88" r="2" fill="#ccc" />
    <text x="26" y="90" fontSize="7.5" fill="#666">1.1 背景介绍</text>
    <rect x="6" y="99" width="108" height="18" fill="#f0f0f0" />
    <circle cx="20" cy="108" r="2" fill="#aaa" />
    <text x="26" y="110" fontSize="7.5" fill="#444">1.2 研究意义</text>
    <circle cx="20" cy="128" r="2" fill="#ccc" />
    <text x="26" y="130" fontSize="7.5" fill="#666">1.3 论文结构</text>
    <text x="14" y="155" fontSize="8" fontWeight="600" fill="#444">第二章：理论基础</text>
    <circle cx="20" cy="172" r="2" fill="#ccc" />
    <text x="26" y="174" fontSize="7.5" fill="#666">2.1 概念定义</text>
    <rect x="120" y="33" width="300" height="227" fill="white" />
    <rect x="120" y="33" width="300" height="28" fill="#f8f8f8" />
    <text x="132" y="51" fontSize="9" fontWeight="600" fill="#666">文档解析</text>
    <text x="300" y="51" fontSize="8" fill="#aaa">已筛选章节</text>
    <text x="135" y="79" fontSize="11" fontWeight="600" fill="#333">1.2 研究意义</text>
    <line x1="135" y1="83" x2="145" y2="83" stroke="#000" strokeWidth="1.5" />
    <text x="135" y="99" fontSize="8" fill="#555">本研究具有重要的理论意义和实践价值。</text>
    <text x="135" y="113" fontSize="8" fill="#555">从理论层面看，本研究探索了 AI 辅助学习的新</text>
    <text x="135" y="127" fontSize="8" fill="#555">范式，为教育技术领域提供了新的视角。</text>
    <text x="135" y="145" fontSize="8" fill="#555">从实践层面看，本研究为在法中国留学生提供</text>
    <text x="135" y="159" fontSize="8" fill="#555">了切实可行的跨语言学习工具与知识管理方案。</text>
    <rect x="135" y="171" width="230" height="50" fill="#f8f8f8" stroke="#eee" strokeWidth="0.5" />
    <rect x="135" y="171" width="230" height="16" fill="#eee" />
    <text x="145" y="182" fontSize="7" fontWeight="600" fill="#555">平台</text><text x="195" y="182" fontSize="7" fontWeight="600" fill="#555">语言</text><text x="245" y="182" fontSize="7" fontWeight="600" fill="#555">功能</text><text x="295" y="182" fontSize="7" fontWeight="600" fill="#555">定价</text>
    <text x="145" y="198" fontSize="7" fill="#666">Coursera</text><text x="195" y="198" fontSize="7" fill="#666">多语言</text><text x="245" y="198" fontSize="7" fill="#666">推荐</text><text x="295" y="198" fontSize="7" fill="#666">$59/月</text>
    <text x="145" y="213" fontSize="7" fill="#666">GreenBean</text><text x="195" y="213" fontSize="7" fill="#666">中/法</text><text x="245" y="213" fontSize="7" fill="#666">深度解析</text><text x="295" y="213" fontSize="7" fill="#666">免费</text>
    <circle cx="355" cy="141" r="6" fill="#dbeafe" />
    <text x="353" y="144" fontSize="6" fontWeight="700" fill="#3b82f6">1</text>
  </svg>
);

/* ---- 2. AI 问答 ---- */
export const ScreenshotAIChat: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 420 260" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <rect x="0" y="0" width="420" height="32" fill="#f8f8f8" />
    <rect x="0" y="16" width="420" height="16" fill="#f8f8f8" />
    <rect x="0" y="32" width="420" height="1" fill="#eee" />
    <circle cx="16" cy="16" r="5" fill="#e5e5e5" />
    <text x="28" y="20" fontSize="10" fontWeight="600" fill="#888">GreenBean</text>
    <rect x="320" y="8" width="24" height="16" fill="#eee" />
    <text x="327" y="19" fontSize="6" fontWeight="500" fill="#666">FR</text>
    <rect x="348" y="8" width="24" height="16" fill="#eee" />
    <circle cx="360" cy="16" r="4" fill="#888" />
    <rect x="376" y="8" width="36" height="16" fill="#000" />
    <text x="385" y="19" fontSize="6" fontWeight="600" fill="white">管理</text>
    <rect x="0" y="33" width="180" height="227" fill="white" stroke="#f0f0f0" strokeWidth="0.5" />
    <rect x="0" y="33" width="180" height="24" fill="#f8f8f8" />
    <text x="10" y="49" fontSize="9" fontWeight="600" fill="#666">文档解析</text>
    <text x="16" y="73" fontSize="9" fontWeight="600" fill="#333">1.1 背景介绍</text>
    <text x="16" y="89" fontSize="7.5" fill="#666">近年来，人工智能技术取得了飞速</text>
    <text x="16" y="101" fontSize="7.5" fill="#666">发展，深刻改变了各行各业的面貌。</text>
    <text x="16" y="117" fontSize="7.5" fill="#666">在教育领域，AI 技术的应用尤为</text>
    <text x="16" y="129" fontSize="7.5" fill="#666">引人注目。本节将介绍本研究的</text>
    <text x="16" y="141" fontSize="7.5" fill="#666">基本背景和动机。</text>
    <rect x="16" y="147" width="140" height="18" fill="#fef3c7" />
    <text x="20" y="159" fontSize="7.5" fill="#92400e">• 在法中国留学生面临的语言</text>
    <text x="20" y="169" fontSize="7.5" fill="#92400e">  与学习障碍</text>
    <rect x="180" y="33" width="240" height="227" fill="white" />
    <rect x="180" y="33" width="240" height="40" fill="#fcfcfc" />
    <rect x="190" y="39" width="18" height="18" fill="#6366f1" />
    <text x="214" y="50" fontSize="9" fontWeight="600" fill="#444">AI 助手</text>
    <text x="214" y="61" fontSize="7" fill="#999">基于课程内容回答</text>
    <rect x="350" y="43" width="50" height="10" fill="#eee" />
    <text x="355" y="50" fontSize="6" fill="#888">150/4096 tokens</text>
    <rect x="234" y="81" width="170" height="26" fill="#000" />
    <text x="240" y="97" fontSize="7.5" fill="white">请解释 1.2 节中提到的研究意义</text>
    <rect x="188" y="115" width="200" height="70" fill="#f0f0f0" />
    <circle cx="198" cy="125" r="6" fill="#6366f1" />
    <text x="206" y="129" fontSize="7.5" fill="#444">根据第 1.2 节内容，本研究</text>
    <text x="198" y="143" fontSize="7.5" fill="#444">研究意义主要体现在两个层面：</text>
    <text x="198" y="159" fontSize="7.5" fill="#444">1. 理论层面：探索 AI 辅助学习</text>
    <text x="198" y="173" fontSize="7.5" fill="#444">   新范式</text>
    <rect x="234" y="193" width="170" height="26" fill="#000" />
    <text x="240" y="209" fontSize="7.5" fill="white">那实践层面的具体方案是什么？</text>
    <rect x="188" y="227" width="80" height="22" fill="#f0f0f0" />
    <circle cx="198" cy="238" r="5" fill="#6366f1" />
    <text x="206" y="241" fontSize="7.5" fill="#888">思考中...</text>
    <rect x="188" y="244" width="190" height="18" fill="#f0f0f0" />
    <text x="196" y="256" fontSize="6.5" fill="#aaa">输入你的问题...</text>
    <rect x="380" y="244" width="20" height="18" fill="#ccc" />
    <path d="M388 249l6 4-6 4" stroke="#fff" strokeWidth="1.5" fill="none" />
  </svg>
);

/* ---- 3. 解析报告 ---- */
export const ScreenshotAnalysis: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 420 260" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <rect x="0" y="0" width="420" height="32" fill="#f8f8f8" />
    <rect x="0" y="16" width="420" height="16" fill="#f8f8f8" />
    <rect x="0" y="32" width="420" height="1" fill="#eee" />
    <circle cx="16" cy="16" r="5" fill="#e5e5e5" />
    <text x="28" y="20" fontSize="10" fontWeight="600" fill="#888">GreenBean</text>
    <rect x="320" y="8" width="24" height="16" fill="#eee" />
    <text x="327" y="19" fontSize="6" fontWeight="500" fill="#666">FR</text>
    <rect x="348" y="8" width="24" height="16" fill="#eee" />
    <circle cx="360" cy="16" r="4" fill="#888" />
    <rect x="376" y="8" width="36" height="16" fill="#000" />
    <text x="385" y="19" fontSize="6" fontWeight="600" fill="white">管理</text>
    <rect x="0" y="33" width="420" height="227" fill="white" />
    <rect x="0" y="33" width="420" height="24" fill="#fcfcfc" stroke="#f0f0f0" strokeWidth="0.5" />
    <rect x="10" y="37" width="50" height="16" fill="#eee" />
    <rect x="66" y="37" width="50" height="16" fill="#eee" />
    <rect x="122" y="37" width="50" height="16" fill="#eee" />
    <text x="20" y="75" fontSize="13" fontWeight="700" fill="#1a1a1a">第三章：方法论</text>
    <line x1="20" y1="79" x2="80" y2="79" stroke="#000" strokeWidth="1.5" />
    <text x="20" y="97" fontSize="10" fontWeight="600" fill="#333">3.1 数据采集</text>
    <text x="20" y="113" fontSize="8" fill="#555">本研究采用混合研究方法，结合定量问卷与</text>
    <text x="20" y="125" fontSize="8" fill="#555">定性访谈来收集数据。问卷面向在法中国留学</text>
    <text x="20" y="137" fontSize="8" fill="#555">生群体，重点调查其学习工具使用现状与需求。</text>
    <rect x="20" y="143" width="280" height="16" fill="#fef3c7" />
    <text x="24" y="155" fontSize="8" fill="#92400e">关键发现：78% 的学生认为语言是理解课程</text>
    <text x="20" y="177" fontSize="10" fontWeight="600" fill="#333">3.2 分析方法</text>
    <text x="20" y="193" fontSize="8" fill="#555">收集到的数据通过主题分析法进行编码和归类。</text>
    <text x="20" y="205" fontSize="8" fill="#555">具体流程包括初始编码、主题提炼、主题审</text>
    <text x="20" y="217" fontSize="8" fill="#555">核和报告撰写四个阶段。</text>
    <circle cx="175" cy="203" r="6" fill="#dbeafe" />
    <text x="173" y="206" fontSize="6" fontWeight="700" fill="#3b82f6">1</text>
    <rect x="310" y="61" width="100" height="120" fill="#f8f8ff" stroke="#e8e8ff" strokeWidth="0.5" />
    <rect x="320" y="69" width="80" height="16" fill="#eef2ff" />
    <text x="330" y="80" fontSize="7" fontWeight="600" fill="#4f46e5">AI 自动摘要</text>
    <text x="322" y="99" fontSize="7" fill="#666">本章介绍了混合研究</text>
    <text x="322" y="111" fontSize="7" fill="#666">方法论，包含问卷</text>
    <text x="322" y="123" fontSize="7" fill="#666">(N=500+) 和深度访谈</text>
    <text x="322" y="135" fontSize="7" fill="#666">两种数据来源，主要</text>
    <text x="322" y="147" fontSize="7" fill="#666">发现在于语言障碍</text>
    <text x="322" y="159" fontSize="7" fill="#666">对学习效率影响显著。</text>
    <line x1="20" y1="240" x2="400" y2="240" stroke="#eee" strokeWidth="0.5" />
    <text x="20" y="250" fontSize="7" fill="#aaa">3 页 · 第 3 章 · 2,340 字符 · 已解析</text>
    <circle cx="370" cy="248" r="4" fill="#22c55e" />
    <text x="378" y="251" fontSize="6" fill="#22c55e">解析完成</text>
  </svg>
);

/* ---- 4. 文件管理 ---- */
export const ScreenshotFileManager: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 420 260" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <defs>
      <filter id="fms"><feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#00000014" /></filter>
    </defs>
    {/* 统一顶栏 */}
    <rect x="0" y="0" width="420" height="32" fill="#f8f8f8" />
    <rect x="0" y="16" width="420" height="16" fill="#f8f8f8" />
    <rect x="0" y="32" width="420" height="1" fill="#eee" />
    <circle cx="16" cy="16" r="5" fill="#e5e5e5" />
    <text x="28" y="20" fontSize="10" fontWeight="600" fill="#888">GreenBean</text>
    <rect x="320" y="8" width="24" height="16" fill="#eee" />
    <text x="327" y="19" fontSize="6" fontWeight="500" fill="#666">FR</text>
    <rect x="348" y="8" width="24" height="16" fill="#eee" />
    <circle cx="360" cy="16" r="4" fill="#888" />
    <rect x="376" y="8" width="36" height="16" fill="#000" />
    <text x="385" y="19" fontSize="6" fontWeight="600" fill="white">管理</text>
    {/* 标题行 */}
    <rect x="0" y="33" width="420" height="26" fill="#fafafa" />
    <text x="14" y="50" fontSize="10" fontWeight="600" fill="#444">文件管理</text>
    {/* 左侧侧边栏 */}
    <rect x="0" y="59" width="76" height="201" fill="#fafafa" stroke="#eee" strokeWidth="0.5" />
    {/* 所有文件 */}
    <rect x="0" y="59" width="76" height="42" fill="#00000008" />
    <path d="M30 67v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2h-5l-2-2H32a2 2 0 0 0-2 2z" stroke="#555" strokeWidth="1" fill="none" />
    <text x="38" y="84" fontSize="6.5" fontWeight="500" fill="#444" textAnchor="middle">所有文件</text>
    <text x="38" y="92" fontSize="5.5" fill="#aaa" textAnchor="middle">8</text>
    <line x1="8" y1="103" x2="68" y2="103" stroke="#eee" strokeWidth="0.5" />
    {/* 课程资料 - 选中态 */}
    <rect x="0" y="107" width="76" height="42" fill="#000" />
    <path d="M30 115v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2h-5l-2-2H32a2 2 0 0 0-2 2z" stroke="#fff" strokeWidth="0.9" fill="none" />
    <text x="38" y="132" fontSize="6.5" fontWeight="500" fill="white" textAnchor="middle">课程资料</text>
    {/* 考试复习 */}
    <path d="M30 163v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2h-5l-2-2H32a2 2 0 0 0-2 2z" stroke="#888" strokeWidth="1" fill="none" />
    <text x="38" y="180" fontSize="6.5" fontWeight="500" fill="#666" textAnchor="middle">考试复习</text>
    <text x="38" y="188" fontSize="5.5" fill="#aaa" textAnchor="middle">1</text>
    {/* 论文参考 */}
    <path d="M30 210v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2h-5l-2-2H32a2 2 0 0 0-2 2z" stroke="#888" strokeWidth="1" fill="none" />
    <text x="38" y="227" fontSize="6.5" fontWeight="500" fill="#666" textAnchor="middle">论文参考</text>
    <text x="38" y="235" fontSize="5.5" fill="#aaa" textAnchor="middle">2</text>
    {/* 右侧文件列表 */}
    <rect x="76" y="59" width="344" height="201" fill="white" />
    {/* 搜索栏 */}
    <rect x="86" y="67" width="160" height="20" fill="#f0f0f0" />
    <text x="102" y="80" fontSize="6.5" fill="#999">搜索文件名...</text>
    {/* 文件1 */}
    <rect x="86" y="96" width="310" height="26" fill="#f5f5f5" />
    <rect x="92" y="100" width="16" height="16" fill="#fee2e2" />
    <text x="100" y="112" fontSize="5" fontWeight="700" fill="#dc2626" textAnchor="middle">PDF</text>
    <text x="113" y="113" fontSize="6.5" fontWeight="500" fill="#444">cours-analyse-s1.pdf</text>
    <text x="320" y="113" fontSize="5.5" fill="#999">2025-09-15</text>
    <text x="370" y="113" fontSize="5.5" fill="#999">12.4 MB</text>
    {/* 文件2 */}
    <rect x="86" y="124" width="310" height="26" fill="transparent" />
    <rect x="92" y="128" width="16" height="16" fill="#dbeafe" />
    <text x="100" y="140" fontSize="5" fontWeight="700" fill="#2563eb" textAnchor="middle">DOC</text>
    <text x="113" y="141" fontSize="6.5" fontWeight="500" fill="#444">TD-économie-chap2.docx</text>
    <text x="320" y="141" fontSize="5.5" fill="#999">2025-10-02</text>
    <text x="370" y="141" fontSize="5.5" fill="#999">3.2 MB</text>
    {/* 文件3 */}
    <rect x="86" y="152" width="310" height="26" fill="transparent" />
    <rect x="92" y="156" width="16" height="16" fill="#fef3c7" />
    <text x="100" y="168" fontSize="5" fontWeight="700" fill="#d97706" textAnchor="middle">PPT</text>
    <text x="113" y="169" fontSize="6.5" fontWeight="500" fill="#444">cours-droit-commercial.pptx</text>
    <text x="320" y="169" fontSize="5.5" fill="#999">2025-10-10</text>
    <text x="370" y="169" fontSize="5.5" fill="#999">45.8 MB</text>
    {/* 文件4 */}
    <rect x="86" y="180" width="310" height="26" fill="transparent" />
    <rect x="92" y="184" width="16" height="16" fill="#fce7f3" />
    <text x="100" y="196" fontSize="5" fontWeight="700" fill="#db2777" textAnchor="middle">IMG</text>
    <text x="113" y="197" fontSize="6.5" fontWeight="500" fill="#444">cours-maths-tableau.webp</text>
    <text x="320" y="197" fontSize="5.5" fill="#999">2025-10-15</text>
    <text x="370" y="197" fontSize="5.5" fill="#999">2.1 MB</text>
    {/* 右键菜单 */}
    <g filter="url(#fms)">
      <rect x="270" y="94" width="115" height="90" fill="white" stroke="#e0e0e0" strokeWidth="0.5" />
      <text x="282" y="111" fontSize="6.5" fontWeight="600" fill="#999">移入文件夹</text>
      <rect x="276" y="118" width="103" height="20" fill="transparent" />
      <path d="M280 124v3a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1h-2l-1-1h-2a1 1 0 0 0-1 1z" stroke="#666" strokeWidth="0.6" fill="none" />
      <text x="290" y="131" fontSize="6.5" fill="#444">考试复习</text>
      <rect x="276" y="140" width="103" height="20" fill="transparent" />
      <path d="M280 146v3a1 1 0 0 0 1 1h5a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1h-2l-1-1h-2a1 1 0 0 0-1 1z" stroke="#666" strokeWidth="0.6" fill="none" />
      <text x="290" y="153" fontSize="6.5" fill="#444">论文参考</text>
      <line x1="282" y1="166" x2="375" y2="166" stroke="#eee" strokeWidth="0.8" />
      <rect x="276" y="168" width="103" height="20" fill="transparent" />
      <polyline points="280 177 282 177 290 177" stroke="#dc2626" strokeWidth="1" fill="none" />
      <path d="M288 177v4a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1v-4m1 0v-1a1 1 0 0 1 1-1h1a1 1 0 0 1 1 1v1" stroke="#dc2626" strokeWidth="1" fill="none" />
      <text x="290" y="182" fontSize="6.5" fill="#dc2626">删除文件</text>
    </g>
  </svg>
);

/* ---- 5. 章节导航 ---- */
export const ScreenshotSectionNav: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg viewBox="0 0 420 260" fill="none" xmlns="http://www.w3.org/2000/svg" {...props}>
    <rect x="0" y="0" width="420" height="32" fill="#f8f8f8" />
    <rect x="0" y="16" width="420" height="16" fill="#f8f8f8" />
    <rect x="0" y="32" width="420" height="1" fill="#eee" />
    <circle cx="16" cy="16" r="5" fill="#e5e5e5" />
    <text x="28" y="20" fontSize="10" fontWeight="600" fill="#888">GreenBean</text>
    <rect x="320" y="8" width="24" height="16" fill="#eee" />
    <text x="327" y="19" fontSize="6" fontWeight="500" fill="#666">FR</text>
    <rect x="348" y="8" width="24" height="16" fill="#eee" />
    <circle cx="360" cy="16" r="4" fill="#888" />
    <rect x="376" y="8" width="36" height="16" fill="#000" />
    <text x="385" y="19" fontSize="6" fontWeight="600" fill="white">管理</text>
    <rect x="0" y="33" width="170" height="227" fill="#fafafa" />
    <rect x="0" y="33" width="170" height="28" fill="#f8f8f8" />
    <text x="12" y="51" fontSize="9" fontWeight="600" fill="#666">章节导航</text>
    <text x="130" y="51" fontSize="7" fill="#aaa">5 个章节</text>
    <rect x="6" y="65" width="158" height="22" fill="#f0f0f0" />
    <text x="20" y="80" fontSize="8" fontWeight="600" fill="#333">第一章：引言</text>
    <text x="32" y="100" fontSize="7.5" fill="#666">1.1 背景介绍</text>
    <rect x="6" y="109" width="158" height="18" fill="#000" />
    <text x="32" y="120" fontSize="7.5" fontWeight="600" fill="white">1.2 研究意义</text>
    <text x="32" y="140" fontSize="7.5" fill="#666">1.3 论文结构</text>
    <rect x="6" y="153" width="158" height="22" fill="#f0f0f0" />
    <text x="20" y="168" fontSize="8" fontWeight="600" fill="#333">第二章：理论基础</text>
    <text x="32" y="188" fontSize="7.5" fill="#666">2.1 概念定义</text>
    <text x="32" y="208" fontSize="7.5" fill="#666">2.2 相关研究</text>
    <text x="20" y="236" fontSize="8" fontWeight="600" fill="#999">第三章：方法论</text>
    <rect x="170" y="33" width="250" height="227" fill="white" />
    <rect x="170" y="33" width="250" height="28" fill="#f8f8f8" />
    <text x="182" y="51" fontSize="9" fontWeight="600" fill="#666">文档解析</text>
    <text x="350" y="51" fontSize="8" fill="#aaa">已筛选章节</text>
    <text x="185" y="79" fontSize="12" fontWeight="700" fill="#1a1a1a">1.2 研究意义</text>
    <line x1="185" y1="83" x2="220" y2="83" stroke="#000" strokeWidth="1.5" />
    <text x="185" y="101" fontSize="8.5" fill="#444">本研究具有重要的理论意义和实践</text>
    <text x="185" y="115" fontSize="8.5" fill="#444">价值，为解决在法中国留学群体的</text>
    <text x="185" y="129" fontSize="8.5" fill="#444">学习适应问题提供了新的思路。</text>
    <rect x="185" y="141" width="220" height="36" fill="#f5f3ff" stroke="#e8e4ff" strokeWidth="0.5" />
    <line x1="189" y1="141" x2="189" y2="177" stroke="#8b5cf6" strokeWidth="2" />
    <text x="198" y="157" fontSize="8" fill="#6d28d9" fontStyle="italic">「实践层面：为在法留学生提供</text>
    <text x="198" y="171" fontSize="8" fill="#6d28d9" fontStyle="italic">跨语言学习工具与知识管理方案」</text>
    <text x="185" y="195" fontSize="8.5" fill="#444">核心理念包括：</text>
    <circle cx="192" cy="205" r="2" fill="#444" />
    <text x="200" y="209" fontSize="8.5" fill="#444">AI 驱动的文档智能解析</text>
    <circle cx="192" cy="219" r="2" fill="#444" />
    <text x="200" y="223" fontSize="8.5" fill="#444">自动生成结构化知识图谱</text>
    <circle cx="192" cy="233" r="2" fill="#444" />
    <text x="200" y="237" fontSize="8.5" fill="#444">上下文感知的智能问答系统</text>
  </svg>
);

export const SCREENSHOT_ILLUSTRATIONS = [
  ScreenshotOverview,
  ScreenshotAIChat,
  ScreenshotAnalysis,
  ScreenshotFileManager,
  ScreenshotSectionNav,
] as const;