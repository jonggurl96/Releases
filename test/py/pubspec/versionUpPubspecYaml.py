import re
from pathlib import Path

path = Path("./pubspec.yaml")
# pubspec.yaml 다음 버전으로 재주껏 정하기
new_version = "1.2.4"

with path.open(encoding="utf-8", newline="") as source:
    lines = source.readlines()

matches = []
for index, line in enumerate(lines):
    if line.startswith("version:"):
        match = re.fullmatch(
            r"""(version:[ \t]*)(['"]?)(\d+\.\d+\.\d+)(?:\+(\d+))?\2([ \t]*(?:#.*)?)(\r?\n?)""",
            line,
        )
        matches.append((index, match))

index, match = matches[0]
print(index, match)
print(f"match group 1) '{match.group(1)}'")
print(f"match group 2) '{match.group(2)}'")
print(f"match group 3) '{match.group(3)}'")
print(f"match group 4) '{match.group(4)}'")
print(f"match group 5) '{match.group(5)}'")
print(f"match group 6) '{match.group(6)}'")
build_number = int(match.group(4) or "0") + 1
lines[index] = (
    f"{match.group(1)}{match.group(2)}{new_version}+{build_number}"
    f"{match.group(2)}{match.group(5)}{match.group(6)}"
)

with path.open("w", encoding="utf-8", newline="") as target:
    target.writelines(lines)
