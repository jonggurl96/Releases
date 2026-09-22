import json
import os
import re
import sys
import tomllib
import xml.etree.ElementTree as ET

project_type = os.environ["PROJECT_TYPE"]
bump_type = os.environ["BUMP_TYPE"]


def get_gradle_version():
    text = open("build.gradle", encoding = "utf-8").read()

    patterns = [
        r'(?m)^\s*version\s*=\s*["\']([^"\']+)["\']',
        r'(?m)^\s*version\s+["\']([^"\']+)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    raise RuntimeError(
        "build.gradle에서 literal version을 찾지 못했습니다."
    )


def get_maven_version():
    root = ET.parse("pom.xml").getroot()

    if root.tag.startswith("{"):
        namespace = root.tag.split("}")[0][1:]
        version = root.find(f"{{{namespace}}}version")
    else:
        version = root.find("version")

    if version is None or not version.text:
        raise RuntimeError(
            "pom.xml의 project.version을 찾지 못했습니다."
        )

    return version.text.strip()


def get_node_version():
    with open("package.json", encoding = "utf-8") as f:
        data = json.load(f)

    version = data.get("version")

    if not version:
        raise RuntimeError(
            "package.json에 version이 없습니다."
        )

    return version


def get_python_version():
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)

    project_version = data.get("project", {}).get("version")

    if project_version:
        return project_version

    poetry_version = (
        data.get("tool", {})
        .get("poetry", {})
        .get("version")
    )

    if poetry_version:
        return poetry_version

    raise RuntimeError(
        "pyproject.toml의 [project] 또는 "
        "[tool.poetry]에서 version을 찾지 못했습니다."
    )


getters = {
    "gradle": get_gradle_version,
    "maven": get_maven_version,
    "node": get_node_version,
    "python": get_python_version,
}

current = getters[project_type]()

# 1.2.3-SNAPSHOT 같은 경우도
# 숫자 부분 1.2.3을 기준으로 계산
match = re.match(
    r'^(\d+)\.(\d+)\.(\d+)',
    current
)

if not match:
    raise RuntimeError(
        f"SemVer 형식이 아닙니다: {current}"
    )

major, minor, patch = map(
    int,
    match.groups()
)

if bump_type == "major":
    major += 1
    minor = 0
    patch = 0

elif bump_type == "minor":
    minor += 1
    patch = 0

elif bump_type == "patch":
    patch += 1

else:
    raise RuntimeError(
        f"지원하지 않는 bump type: {bump_type}"
    )

new_version = f"{major}.{minor}.{patch}"
tag = f"v{new_version}"

print(f"Current version : {current}")
print(f"New version     : {new_version}")
print(f"Tag             : {tag}")

github_output = os.environ["GITHUB_OUTPUT"]

with open(github_output, "a", encoding = "utf-8") as f:
    f.write(f"current={current}\n")
    f.write(f"new={new_version}\n")
    f.write(f"tag={tag}\n")
