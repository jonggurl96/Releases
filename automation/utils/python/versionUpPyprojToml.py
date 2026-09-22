import os
import re
import tomllib

path = "pyproject.toml"
new_version = os.environ["NEW_VERSION"]

with open(path, "rb") as f:
    data = tomllib.load(f)

if data.get("project", {}).get("version"):
    target_section = "project"

elif (
        data.get("tool", {})
                .get("poetry", {})
                .get("version")
):
    target_section = "tool.poetry"

else:
    raise RuntimeError(
        "pyproject.toml에서 version을 찾지 못했습니다."
    )

with open(path, encoding = "utf-8") as f:
    lines = f.readlines()

current_section = None
replaced = False

for index, line in enumerate(lines):

    section_match = re.match(
        r'^\s*\[([^\]]+)]\s*$',
        line
    )

    if section_match:
        current_section = section_match.group(1)
        continue

    if current_section != target_section:
        continue

    version_match = re.match(
        r'^(\s*version\s*=\s*)(["\'])([^"\']+)(["\'])(.*)$',
        line
    )

    if version_match:
        quote = version_match.group(2)

        lines[index] = (
                version_match.group(1)
                + quote
                + new_version
                + quote
                + version_match.group(5)
                + "\n"
        )

        replaced = True
        break

if not replaced:
    raise RuntimeError(
        "pyproject.toml version 수정 실패"
    )

with open(path, "w", encoding = "utf-8") as f:
    f.writelines(lines)
