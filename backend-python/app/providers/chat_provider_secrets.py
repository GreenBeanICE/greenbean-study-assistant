"""Chat/LLM Provider 本地 secrets 配置读取与解析。"""

import json
from pathlib import Path
from typing import Any

from app.entities.provider_config import ProviderConfig
from app.enums.api_mode import ApiMode
from app.providers.base import ProviderConfigurationError

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHAT_PROVIDERS_SECRETS_PATH = (
    BACKEND_ROOT / "secrets" / "chat_providers.json"
)
CHAT_SECRET_REF_PREFIX = "secret://chat.providers."
CHAT_SECRET_REF_SUFFIX = ".api_key"


class ChatProviderSecretsError(ProviderConfigurationError):
    """Chat/LLM Provider secrets 无法安全加载。"""


def chat_api_key_secret_ref(provider_name: str) -> str:
    """返回 provider_configs.api_key 中应持久化的密钥引用。"""

    return f"{CHAT_SECRET_REF_PREFIX}{provider_name}{CHAT_SECRET_REF_SUFFIX}"


def load_active_chat_provider_config(
    secrets_path: str | Path | None = None,
) -> ProviderConfig:
    """读取 active chat provider，并返回只含非敏感信息的 ProviderConfig。"""

    path = Path(secrets_path) if secrets_path is not None else DEFAULT_CHAT_PROVIDERS_SECRETS_PATH
    payload = _read_json_object(path, "Chat provider secrets")
    active = _required_string(payload, "active", "Chat provider secrets 缺少 active")
    providers = payload.get("providers")
    if not isinstance(providers, dict):
        raise ChatProviderSecretsError("Chat provider secrets 缺少 providers")

    raw_config = providers.get(active)
    if not isinstance(raw_config, dict):
        raise ChatProviderSecretsError(
            f"Chat provider active 指向不存在的 provider: {active}"
        )

    api_mode = _required_string(
        raw_config,
        "api_mode",
        f"Chat provider {active} 缺少 api_mode",
    )
    if api_mode != ApiMode.OPENAI_COMPAT.value:
        raise ChatProviderSecretsError(f"不支持的 Chat provider api_mode: {api_mode}")

    _required_string(
        raw_config,
        "api_key",
        f"Chat provider {active} 缺少 api_key",
    )
    api_host = _required_string(
        raw_config,
        "api_host",
        f"Chat provider {active} 缺少 api_host",
    )
    model_id = _required_string(
        raw_config,
        "model_id",
        f"Chat provider {active} 缺少 model_id",
    )
    display_name = _required_string(
        raw_config,
        "display_name",
        f"Chat provider {active} 缺少 display_name",
    )

    return ProviderConfig(
        name=active,
        api_mode=ApiMode.OPENAI_COMPAT,
        api_key=chat_api_key_secret_ref(active),
        api_host=api_host,
        api_path=_optional_string(raw_config, "api_path") or "/v1/chat/completions",
        model_id=model_id,
        display_name=display_name,
        context_window=_optional_positive_int(raw_config, "context_window", 65536),
        max_output_tokens=_optional_positive_int(
            raw_config,
            "max_output_tokens",
            8192,
        ),
        is_active=True,
    )


def resolve_chat_api_key(
    value: str,
    secrets_path: str | Path | None = None,
) -> str:
    """解析 provider_configs.api_key 中的 secret:// 引用。

    非 secret:// 值保持旧行为，用于兼容旧配置和既有测试。
    """

    if not value.startswith(CHAT_SECRET_REF_PREFIX):
        return value

    provider_name = _provider_name_from_secret_ref(value)
    path = Path(secrets_path) if secrets_path is not None else DEFAULT_CHAT_PROVIDERS_SECRETS_PATH
    payload = _read_json_object(path, "Chat provider secrets")
    providers = payload.get("providers")
    if not isinstance(providers, dict):
        raise ChatProviderSecretsError("Chat provider secrets 缺少 providers")

    raw_config = providers.get(provider_name)
    if not isinstance(raw_config, dict):
        raise ChatProviderSecretsError(
            f"Chat provider secret 引用指向不存在的 provider: {provider_name}"
        )

    return _required_string(
        raw_config,
        "api_key",
        f"Chat provider {provider_name} 缺少 api_key",
    )


def _provider_name_from_secret_ref(value: str) -> str:
    if not value.endswith(CHAT_SECRET_REF_SUFFIX):
        raise ChatProviderSecretsError("Chat provider secret 引用格式无效")
    provider_name = value[
        len(CHAT_SECRET_REF_PREFIX) : -len(CHAT_SECRET_REF_SUFFIX)
    ]
    if not provider_name.strip():
        raise ChatProviderSecretsError("Chat provider secret 引用缺少 provider 名称")
    return provider_name


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ChatProviderSecretsError(f"{label} 文件不存在: {path}") from exc
    except OSError as exc:
        raise ChatProviderSecretsError(f"无法读取 {label} 文件: {path}") from exc

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ChatProviderSecretsError(f"{label} 不是有效 JSON") from exc
    if not isinstance(payload, dict):
        raise ChatProviderSecretsError(f"{label} 顶层必须是 JSON object")
    return payload


def _required_string(
    payload: dict[str, Any],
    key: str,
    message: str,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ChatProviderSecretsError(message)
    return value.strip()


def _optional_string(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ChatProviderSecretsError(f"Chat provider {key} 必须是非空字符串")
    return value.strip()


def _optional_positive_int(
    payload: dict[str, Any],
    key: str,
    default: int,
) -> int:
    value = payload.get(key, default)
    if not isinstance(value, int) or value <= 0:
        raise ChatProviderSecretsError(f"Chat provider {key} 必须是正整数")
    return value
