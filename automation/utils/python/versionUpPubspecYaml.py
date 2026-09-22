import os
import re
from pathlib import Path

path = Path("pubspec.yaml")
new_version = os.environ["NEW_VERSION"]

if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", new_version):
    raise RuntimeError("NEW_VERSION 형식이 올바르지 않습니다.")

with path.open(encoding="utf-8", newline="") as source:
    lines = source.readlines()

matches = []
for index, line in enumerate(lines):
    if line.startswith("version:"):
        match = re.fullmatch(
            r"""(version:[ \t]*)(['"]?)(\d+\.\d+\.\d+)(?:\+(\d+))?\2([ \t]*(?:#.*)?)(\r?\n?)""",
            line,
        )
        if not match:
            raise RuntimeError("pubspec.yaml의 version 형식이 올바르지 않습니다.")
        matches.append((index, match))

if len(matches) != 1:
    raise RuntimeError("pubspec.yaml에 최상위 version이 정확히 하나 있어야 합니다.")

index, match = matches[0]
build_number = int(match.group(4) or "0") + 1
lines[index] = (
    f"{match.group(1)}{match.group(2)}{new_version}+{build_number}"
    f"{match.group(2)}{match.group(5)}{match.group(6)}"
)

with path.open("w", encoding="utf-8", newline="") as target:
    target.writelines(lines)
