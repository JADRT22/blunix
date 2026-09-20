#!/usr/bin/env python3
"""Extrai a seção de uma versão do CHANGELOG.md para as release notes.

Uso: python3 tools/extract_changelog.py 1.1
Procura por "## v1.1" (ou "## 1.1") e imprime tudo até o próximo "## ".
Falha (exit 1) se a seção não existir — o workflow usa o fallback.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: extract_changelog.py <versão>", file=sys.stderr)
        return 2
    version = sys.argv[1].lstrip("v")
    changelog = Path(__file__).resolve().parent.parent / "CHANGELOG.md"
    if not changelog.is_file():
        print(f"{changelog} não encontrado", file=sys.stderr)
        return 1

    pattern = re.compile(rf"^## v?{re.escape(version)}\b.*$", re.MULTILINE)
    text = changelog.read_text(encoding="utf-8")
    m = pattern.search(text)
    if not m:
        print(f"seção da versão {version} não encontrada", file=sys.stderr)
        return 1
    start = m.start()
    nxt = re.search(r"^## ", text[m.end():], re.MULTILINE)
    end = m.end() + nxt.start() if nxt else len(text)
    print(text[start:end].strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
