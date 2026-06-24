"""Provider 配置的 JSON 文件仓库。

负责 provider_configs.json 的读写、序列化与原子替换。
不依赖业务 SQLite，避免与应用数据耦合。
"""
import json
import os
import threading
from pathlib import Path

from app.entities.provider_config import ProviderConfig
from app.enums.purpose import Purpose


class ProviderConfigRepository:
    def __init__(self, file_path: str | os.PathLike) -> None:
        self._path = Path(file_path)
        self._lock = threading.Lock()

    def _read(self) -> list[ProviderConfig]:
        if not self._path.exists():
            return []
        with self._path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        items = payload.get("providers", []) if isinstance(payload, dict) else []
        return [ProviderConfig(**item) for item in items]

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
