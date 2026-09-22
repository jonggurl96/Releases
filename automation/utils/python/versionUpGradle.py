import os
import re

path = "build.gradle"
new_version = os.environ["NEW_VERSION"]

with open(path, encoding = "utf-8") as f:
    text = f.read()

patterns = [
    re.compile(
        r'(?m)^(\s*version\s*=\s*)(["\'])([^"\']+)(["\'])(.*)$'
    ),
    re.compile(
        r'(?m)^(\s*version\s+)(["\'])([^"\']+)(["\'])(.*)$'
    ),
]

replaced = False

for pattern in patterns:
    def replace(match):
        quote = match.group(2)

        return (
                match.group(1)
                + quote
                + new_version
                + quote
                + match.group(5)
        )


    text, count = pattern.subn(
        replace,
        text,
        count = 1
    )

    if count:
        replaced = True
        break

if not replaced:
    raise RuntimeError(
        "build.gradle version 수정 실패"
    )

with open(path, "w", encoding = "utf-8") as f:
    f.write(text)
