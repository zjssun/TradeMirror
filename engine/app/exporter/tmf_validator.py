from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

REQUIRED_FILES = {"manifest.json", "prompt.md", "profile.json", "statistics.json", "trades.json", "contexts.json", "trade_events.json", "trading_narrative.md", "trading_timeline.json", "validation.json"}
_SUPPORTED_FORMATS = {"1.0", "1.1"}
_PROVENANCE_FIELDS = {"schema_version", "provider", "provider_version", "entry_policy", "exit_policy"}
_ENTRY_POLICY = "fully_closed_candles_before_open_time"
_EXIT_POLICY = "fully_closed_candles_at_or_before_close_time"


def validate_tmf(path: Path) -> dict:
    if path.suffix != ".tmf":
        raise ValueError("导出文件必须使用 .tmf 扩展名。")
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        missing = REQUIRED_FILES - names
        if missing:
            raise ValueError(f"TMF 缺少必需文件：{', '.join(sorted(missing))}。")
        manifest = json.loads(archive.read("manifest.json"))
        format_version = manifest.get("format_version", "1.0")
        if format_version not in _SUPPORTED_FORMATS:
            raise ValueError("TMF 格式版本不受支持。")
        _validate_manifest_files(archive, names, manifest)
        options = manifest.get("options")
        if not isinstance(options, dict) or not isinstance(options.get("include_charts"), bool):
            raise ValueError("TMF 清单选项无效。")
        charts = [name for name in names if name.startswith("charts/") and name.endswith(".png")]
        if options["include_charts"] and len(charts) != manifest.get("trade_count"):
            raise ValueError("TMF 图表数量与交易数量不一致。")
        _validate_replay(archive, names, manifest, options["include_charts"])
        if format_version == "1.1":
            _validate_indicator_provenance(archive, manifest)
    return {"passed": True, "file_count": len(names)}


def _validate_manifest_files(archive: zipfile.ZipFile, names: set[str], manifest: dict) -> None:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError("TMF 清单文件列表无效。")
    for entry in files:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or not isinstance(entry.get("sha256"), str):
            raise ValueError("TMF 清单文件条目无效。")
        if entry["path"] not in names:
            raise ValueError("TMF 清单引用了不存在的文件。")
        digest = hashlib.sha256(archive.read(entry["path"])).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError("TMF 文件校验和不匹配。")


def _validate_replay(archive: zipfile.ZipFile, names: set[str], manifest: dict, include_charts: bool) -> None:
    kind = manifest.get("export_kind")
    if kind not in {None, "trade_collection", "trade_replay"}:
        raise ValueError("TMF 导出类型无效。")
    if kind != "trade_replay":
        return
    if "replay.json" not in names:
        raise ValueError("回放 TMF 缺少 replay.json。")
    replay = json.loads(archive.read("replay.json"))
    if replay.get("schema_version") != "1.0":
        raise ValueError("回放 TMF schema 版本不受支持。")
    candles = replay.get("candles")
    if not isinstance(candles, list) or not candles or replay.get("initial_cursor", -1) > replay.get("cursor", -1) or replay.get("cursor", -1) >= len(candles):
        raise ValueError("回放 TMF 进度无效。")
    if include_charts and "replay/replay.png" not in names:
        raise ValueError("回放 TMF 缺少回放图表。")


def _validate_indicator_provenance(archive: zipfile.ZipFile, manifest: dict) -> None:
    aggregate = manifest.get("indicator_engine")
    contexts = json.loads(archive.read("contexts.json"))
    if not isinstance(contexts, list):
        raise ValueError("TMF 上下文数据无效。")
    provenances = []
    for context in contexts:
        if not isinstance(context, dict) or context.get("status") != "completed":
            continue
        market_context = ((context.get("context") or {}).get("market_context") or {})
        provenance = market_context.get("indicator_provenance")
        if provenance is not None:
            _validate_provenance(provenance)
            provenances.append(provenance)
    if not provenances:
        if aggregate is not None:
            raise ValueError("TMF 指标来源与上下文不一致。")
        return
    _validate_provenance(aggregate)
    if any(provenance != aggregate for provenance in provenances):
        raise ValueError("TMF 指标来源与上下文不一致。")


def _validate_provenance(provenance: object) -> None:
    if not isinstance(provenance, dict) or set(provenance) != _PROVENANCE_FIELDS:
        raise ValueError("TMF 指标来源字段无效。")
    if provenance["schema_version"] != "1.0":
        raise ValueError("TMF 指标来源 schema 版本不受支持。")
    if not isinstance(provenance["provider"], str) or not provenance["provider"].strip():
        raise ValueError("TMF 指标来源 provider 无效。")
    if not isinstance(provenance["provider_version"], str) or not provenance["provider_version"].strip():
        raise ValueError("TMF 指标来源 provider 版本无效。")
    if provenance["entry_policy"] != _ENTRY_POLICY or provenance["exit_policy"] != _EXIT_POLICY:
        raise ValueError("TMF 指标来源 K线时间边界策略无效。")
