from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

REQUIRED_FILES = {"manifest.json", "prompt.md", "profile.json", "statistics.json", "trades.json", "contexts.json", "trade_events.json", "trading_narrative.md", "trading_timeline.json", "validation.json"}


def validate_tmf(path: Path) -> dict:
    if path.suffix != ".tmf":
        raise ValueError("导出文件必须使用 .tmf 扩展名。")
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        missing = REQUIRED_FILES - names
        if missing:
            raise ValueError(f"TMF 缺少必需文件：{', '.join(sorted(missing))}。")
        manifest = json.loads(archive.read("manifest.json"))
        for entry in manifest["files"]:
            if entry["path"] not in names:
                raise ValueError("TMF 清单引用了不存在的文件。")
            digest = hashlib.sha256(archive.read(entry["path"])).hexdigest()
            if digest != entry["sha256"]:
                raise ValueError("TMF 文件校验和不匹配。")
        charts = [name for name in names if name.startswith("charts/") and name.endswith(".png")]
        if manifest["options"]["include_charts"] and len(charts) != manifest["trade_count"]:
            raise ValueError("TMF 图表数量与交易数量不一致。")
    return {"passed": True, "file_count": len(names)}
