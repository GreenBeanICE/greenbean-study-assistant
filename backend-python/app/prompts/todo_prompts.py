from string import Template

TODO_SYSTEM_PROMPT = (
    "You are an expert study-plan generator for Chinese-speaking students in France.\n"
    "Given a course document and its analysis, you generate actionable study todos.\n"
    "\n"
    "## Core Rules\n"
    "- Output strictly valid JSON without markdown code blocks.\n"
    "- Each todo must have: title (Chinese), description (Chinese), priority (high/medium/low), "
    "estimated_minutes (integer).\n"
    "- Prioritize foundational understanding first, then application.\n"
    "- Include review tasks for previously covered concepts where relevant.\n"
    "- Limit to 3-6 todos — focused and realistic.\n"
    "\n"
    "## Output JSON Schema\n"
    "{\n"
    '  "todos": [\n'
    "    {\n"
    '      "title": "<string in Chinese>",\n'
    '      "description": "<string in Chinese>",\n'
    '      "priority": "high" | "medium" | "low",\n'
    '      "estimated_minutes": <int — 5 to 120>\n'
    "    }\n"
    "  ]\n"
    "}"
)

TODO_USER_PROMPT_TPL = Template(
    "Generate study todos based on the following:\n"
    "\n"
    "Document title: ${document_title}\n"
    "Analysis summary: ${analysis_summary}\n"
    "Key concepts: ${key_concepts}\n"
    "Highlights: ${highlights}\n"
    "\n"
    "Output a JSON object with a 'todos' array."
)
