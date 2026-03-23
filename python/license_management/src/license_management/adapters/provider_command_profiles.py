from __future__ import annotations

"""Provider start-option profile loader and resolver.

English:
This module centralizes provider-specific command option rules used to compose
startup commands, and reads them from an external JSON file so option changes
do not require source-code edits.

Chinese:
本模块用于集中管理 provider 启动参数策略：从外部 JSON 读取规则并生成命令
选项，避免每次改参数都修改 Python 源码。

Config source / 配置来源:
    src/license_management/config/provider_start_options.json

Supported keys / 支持字段:
    - start_file_option: primary option before license file path / 许可证文件前的
      主选项（例如 FlexNet 的 -c）
    - log_option: optional log option token / 可选日志参数（例如 -l）
    - log_file_template: optional log file template / 日志文件模板
      placeholders / 占位符:
        - {date}: current date in YYYY-MM-DD / 当前日期
        - {license_dir}: directory of license_file_path / 许可证文件所在目录

Design notes / 设计说明:
    - Provider matching is case-insensitive / provider 名大小写不敏感
    - Missing provider falls back to default profile / 未命中时回退 default
    - Config is cached by lru_cache(maxsize=1) / 配置使用单实例缓存减少 I/O
"""

from dataclasses import dataclass
from datetime import date
import json
from functools import lru_cache
import ntpath
from pathlib import Path
from typing import cast


@dataclass(slots=True, frozen=True)
class ProviderCommandProfile:
    """Resolved option profile for one provider / 单个 provider 的已解析配置。"""

    start_file_option: str
    log_option: str = ""
    log_file_template: str = ""


@dataclass(slots=True, frozen=True)
class ProviderCommandProfileConfig:
    """In-memory profile map / 内存中的 default 与 providers 映射。"""

    default: ProviderCommandProfile
    providers: dict[str, ProviderCommandProfile]


@lru_cache(maxsize=1)
def _load_profiles() -> ProviderCommandProfileConfig:
    """Load and normalize profiles from JSON / 从 JSON 加载并归一化配置。

    English:
    Returns a usable config object even when raw JSON is partially malformed.

    Chinese:
    即使 JSON 存在部分脏数据，也会尽量返回可用配置；非 dict 结构会被安全忽略。
    """

    config_path = Path(__file__).resolve().parents[1] / "config" / "provider_start_options.json"
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        # Safe fallback if config file contains a non-object payload.
        return ProviderCommandProfileConfig(
            default=ProviderCommandProfile(start_file_option="-c"),
            providers={},
        )
    data = cast(dict[object, object], raw)

    default_obj_raw = data.get("default", {})
    default_obj = _to_str_object_dict(default_obj_raw)
    default_option = str(default_obj.get("start_file_option", "-c")).strip() or "-c"
    default_log_option = str(default_obj.get("log_option", "")).strip()
    default_log_template = str(default_obj.get("log_file_template", "")).strip()
    default_profile = ProviderCommandProfile(
        start_file_option=default_option,
        log_option=default_log_option,
        log_file_template=default_log_template,
    )

    raw_providers_obj = data.get("providers", {})
    raw_providers_untyped = _to_str_object_dict(raw_providers_obj)
    providers: dict[str, ProviderCommandProfile] = {}
    for name, profile_obj_raw in raw_providers_untyped.items():
        profile_obj = _to_str_object_dict(profile_obj_raw)
        if not profile_obj:
            continue
        option = str(profile_obj.get("start_file_option", default_option)).strip() or default_option
        log_option = str(profile_obj.get("log_option", default_log_option)).strip()
        log_template = str(profile_obj.get("log_file_template", default_log_template)).strip()
        providers[name.strip().lower()] = ProviderCommandProfile(
            start_file_option=option,
            log_option=log_option,
            log_file_template=log_template,
        )

    return ProviderCommandProfileConfig(default=default_profile, providers=providers)


def resolve_start_file_option(provider: str) -> str:
    """Resolve primary start option / 解析主启动选项。

    English:
    Kept for call sites that only need the first option token.

    Chinese:
    该函数用于只需要主选项（如 -c）的调用场景。
    """

    config = _load_profiles()
    profile = config.providers.get(provider.strip().lower())
    if profile is None:
        return config.default.start_file_option
    return profile.start_file_option


def resolve_start_option_tokens(
    provider: str,
    *,
    today: date | None = None,
    license_file_path: str = "",
) -> tuple[str, ...]:
    """Resolve full option token tuple / 解析完整选项 token 元组。

    Output / 输出格式:
        (start_file_option,) or
        (start_file_option, log_option, resolved_log_file)

    Placeholder expansion / 占位符展开:
        {date} -> YYYY-MM-DD
        {license_dir} -> directory of license_file_path / 许可证目录
    """

    config = _load_profiles()
    profile = config.providers.get(provider.strip().lower(), config.default)
    tokens: list[str] = [profile.start_file_option]
    if profile.log_option and profile.log_file_template:
        now = today or date.today()
        license_dir = ntpath.dirname(license_file_path)
        log_file = (
            profile.log_file_template.replace("{date}", now.isoformat())
            .replace("{license_dir}", license_dir)
            .replace("//", "/")
        )
        tokens.extend([profile.log_option, log_file])
    return tuple(tokens)


def _to_str_object_dict(value: object) -> dict[str, object]:
    """Normalize unknown object to dict[str, object] / 将未知对象归一化为字符串键字典。"""

    if not isinstance(value, dict):
        return {}

    typed = cast(dict[object, object], value)
    normalized: dict[str, object] = {}
    for key, item in typed.items():
        if isinstance(key, str):
            normalized[key] = item
    return normalized


