"""Provider 配置的 JSON 文件仓库。

负责 provider_configs.json 的读写、序列化与原子替换。
不依赖业务 SQLite，避免与应用数据耦合。
"""
import json
import os
import sqlite3
import threading
from pathlib import Path

from app.entities.provider_config import ProviderConfig
from app.enums.purpose import Purpose

_LEGACY_DATABASE_NAME = "greenbean-study-assistant.sqlite3"
_LEGACY_API_MODE_MAP = {"openai_compat": "openai-compat"}


class ProviderConfigRepository:
    def __init__(self, file_path: str | os.PathLike) -> None:
        self._path = Path(file_path)
        self._lock = threading.Lock()

    def _read(self) -> list[ProviderConfig]:
        if not self._path.exists():
            configs = self._migrate_legacy_sqlite()
            if configs:
                self._write(configs)
            return configs
        with self._path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        items = payload.get("providers", []) if isinstance(payload, dict) else []
        return [ProviderConfig(**item) for item in items]

    def _migrate_legacy_sqlite(self) -> list[ProviderConfig]:
        legacy_database_path = self._path.with_name(_LEGACY_DATABASE_NAME)
        if not legacy_database_path.exists():
            return []
        try:
            with sqlite3.connect(legacy_database_path) as connection:
                rows = connection.execute(
                    """
                    SELECT id, name, api_mode, api_key, api_host, api_path, model_id,
                           display_name, context_window, max_output_tokens, is_active,
                           created_at, updated_at
                    FROM provider_configs
                    ORDER BY created_at ASC, id ASC
                    """
                ).fetchall()
        except sqlite3.Error:
            return []

        return [
            ProviderConfig(
                id=row[0],
                name=row[1],
                api_mode=_LEGACY_API_MODE_MAP.get(row[2], row[2]),
                api_key=row[3],
                api_host=row[4],
                api_path=row[5],
                model_id=row[6],
                display_name=row[7],
                context_window=row[8],
                max_output_tokens=row[9],
                is_active=bool(row[10]),
                created_at=row[11],
                updated_at=row[12],
                purpose=Purpose.CHAT,
                embedding_dimension=None,
            )
            for row in rows
        ]

    def _write(self, configs: list[ProviderConfig]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"providers": [c.model_dump(mode="json") for c in configs]}
        tmp_path = self._path.with_suffix(self._path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self._path)

    def list_all(self) -> list[ProviderConfig]:
        with self._lock:
            return self._read()

    def list_by_purpose(self, purpose: Purpose) -> list[ProviderConfig]:
        with self._lock:
            return [c for c in self._read() if c.purpose == purpose]

    def get_by_id(self, config_id: str) -> ProviderConfig | None:
        with self._lock:
            for config in self._read():
                if config.id == config_id:
                    return config
            return None

    def get_active_by_purpose(self, purpose: Purpose) -> ProviderConfig | None:
        with self._lock:
            for config in self._read():
                if config.purpose == purpose and config.is_active:
                    return config
            return None

    def save(self, config: ProviderConfig) -> ProviderConfig:
        with self._lock:
            configs = self._read()
            for index, existing in enumerate(configs):
                if existing.id == config.id:
                    configs[index] = config
                    break
            else:
                configs.append(config)
            self._write(configs)
        return config

    def delete(self, config_id: str) -> bool:
        with self._lock:
            configs = self._read()
            remaining = [c for c in configs if c.id != config_id]
            if len(remaining) == len(configs):
                return False
            self._write(remaining)
            return True

    def deactivate_by_purpose(self, purpose: Purpose) -> None:
        with self._lock:
            configs = self._read()
            changed = False
            for index, config in enumerate(configs):
                if config.purpose == purpose and config.is_active:
                    configs[index] = config.model_copy(update={"is_active": False})
                    changed = True
            if changed:
                self._write(configs)
