from app.prompts.todo_prompts import TODO_SYSTEM_PROMPT, TODO_USER_PROMPT_TPL


def test_todo_prompts_import_and_template():
    assert "study-plan" in TODO_SYSTEM_PROMPT
    result = TODO_USER_PROMPT_TPL.substitute(
        document_title="Doc",
        analysis_summary="Sum",
        key_concepts="A,B",
        highlights="H",
    )
    assert "Doc" in result
    assert "A,B" in result
