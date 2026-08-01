from __future__ import annotations

import csv
import io

ENCODINGS = ("utf-8-sig", "utf-8", "gb18030", "gbk")


def decode_csv(content: bytes) -> tuple[str, str]:
    for encoding in ENCODINGS:
        try:
            return content.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("无法识别 CSV 文件编码，请使用 UTF-8 或 GBK 编码后重试。")


def parse_csv(content: bytes) -> tuple[list[str], list[dict[str, str]], str, str]:
    text, encoding = decode_csv(content)
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        raise ValueError("CSV 文件缺少表头。")
    columns = [column.strip() for column in reader.fieldnames]
    rows = [{key.strip(): (value or "").strip() for key, value in row.items() if key is not None} for row in reader]
    return columns, rows, encoding, dialect.delimiter
