def build_prompt(manifest: dict, profile: dict, statistics: dict) -> str:
    return f"""# TradeMirror 历史交易复盘请求

请仅基于本 TMF 归档中的历史数据完成复盘，不预测未来市场，不提供下单、仓位或交易指令。

- 交易数：{statistics['trade_count']}
- 数据来源：{manifest.get('source') or '、'.join(manifest.get('sources', [])) or '未标注'}
- 覆盖品种：{'、'.join(manifest.get('symbols', [])) or '未标注'}
- 导出是否脱敏：{'是' if manifest['options']['redact_source_identity'] else '否'}
- 交易风格：{profile['style']}
- 净盈亏：{statistics['net_profit']}
{_replay_prompt(manifest)}

请输出：
1. 数据覆盖和局限性；
2. 可重复出现的执行、风险与市场环境模式；
3. 有证据支持的优点与改进点；
4. 不确定项和需要补充的数据。

K线及 MFE/MAE 来自 OHLC 区间近似；没有上下文的交易不得被推断为不存在或失败。

如 manifest 中含有 indicator_engine，交易上下文中的技术指标为本地 Python Engine 使用已完整收盘的历史 K 线计算的快照，仅用于复盘，不是预测或交易信号。
"""


def _replay_prompt(manifest: dict) -> str:
    return "- 本归档包含 replay.json：使用其中的已解析周期、回放范围和播放位置分析历史回放。" if manifest.get("export_kind") == "trade_replay" else ""
