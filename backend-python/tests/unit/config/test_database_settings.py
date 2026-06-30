from pathlib import Path


def test_default_database_path_is_absolute_and_independent_from_cwd(monkeypatch):
    from app.config.settings import get_default_database_path

    project_root = Path(__file__).resolve().parents[4]
    backend_root = project_root / "backend-python"

    monkeypatch.chdir(project_root)
    path_from_project_root = get_default_database_path()

    monkeypatch.chdir(backend_root)
    path_from_backend_root = get_default_database_path()

    assert path_from_project_root == path_from_backend_root
    assert path_from_project_root.is_absolute()
    assert path_from_project_root == project_root / "data" / "greenbean-study-assistant.sqlite3"


def test_database_url_environment_override_uses_configured_sqlite_url(
    monkeypatch,
    tmp_path,
):
    from app.config.settings import get_database_settings

    database_path = tmp_path / "override.sqlite3"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = get_database_settings()

    assert settings.database_url == database_url
    assert settings.database_path == database_path
