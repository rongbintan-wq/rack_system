#!/usr/bin/env python3
"""检查项目版本号一致性（提交前校验用）。

权威版本来源：CHANGELOG.md 最新 [X.Y.Z] 条目。
校验载体：
  - backend/app/main.py   -> FastAPI(version="X.Y.Z")
  - web/package.json      -> "version": "X.Y.Z"
不一致则打印差异并以 exit(1) 退出，便于接入提交前检查 / CI。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(path: Path) -> str:
    if not path.exists():
        raise SystemExit(f"[ERROR] 文件不存在: {path}")
    return path.read_text(encoding="utf-8")


def changelog_version(text: str) -> str:
    # 取所有形如 [1.2.0] 的条目中语义版本号最大者（即最新发布版本，
    # 不依赖 CHANGELOG 排列顺序：本仓库为正序，最新在底部）
    versions = re.findall(r"\[(\d+\.\d+\.\d+)\]", text)
    if not versions:
        raise SystemExit("[ERROR] CHANGELOG.md 中未找到版本号 [X.Y.Z]")
    return max(versions, key=lambda v: tuple(int(x) for x in v.split(".")))


def main_version(text: str) -> str:
    m = re.search(r'FastAPI\([^)]*version\s*=\s*["\']([^"\']+)["\']', text)
    if not m:
        raise SystemExit("[ERROR] backend/app/main.py 中未找到 FastAPI(version=...)")
    return m.group(1)


def pkg_version(text: str) -> str:
    try:
        return json.loads(text)["version"]
    except Exception as e:  # noqa: BLE001
        raise SystemExit(f"[ERROR] 解析 web/package.json 失败: {e}")


def main() -> None:
    cl = changelog_version(read(ROOT / "CHANGELOG.md"))
    main_v = main_version(read(ROOT / "backend" / "app" / "main.py"))
    pkg_v = pkg_version(read(ROOT / "web" / "package.json"))

    print(f"CHANGELOG.md (权威) : {cl}")
    print(f"backend/app/main.py: {main_v}")
    print(f"web/package.json   : {pkg_v}")

    if cl == main_v == pkg_v:
        print("\n[OK] 版本号一致")
        sys.exit(0)

    diffs = []
    if cl != main_v:
        diffs.append(f"main.py ({main_v}) != CHANGELOG ({cl})")
    if cl != pkg_v:
        diffs.append(f"package.json ({pkg_v}) != CHANGELOG ({cl})")
    print("\n[FAIL] 版本号不一致，请先以 CHANGELOG.md 为准统一后再提交：")
    for d in diffs:
        print("  - " + d)
    sys.exit(1)


if __name__ == "__main__":
    main()
