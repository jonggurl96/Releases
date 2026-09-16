# 커밋 접두사 기반 자동 버전 관리

`.github/workflows/release.yml`은 `main`에 push된 마지막 커밋의 제목을 확인하여 Git 버전 태그와 GitHub Release를 생성합니다. 이 문서는 현재 동작을 요약하고 Python, Node.js, Spring Boot, Kotlin 프로젝트의 버전 값을 같은 버전으로 갱신하는 확장 예제를 제공합니다.

현재 저장소에는 워크플로만 있으며, 아래 프로젝트별 코드는 적용 예제입니다. README를 추가하는 것만으로 버전 파일 수정이나 빌드가 자동 실행되지는 않습니다.

## 목차

- [1. release.yml 동작 요약](#1-releaseyml-동작-요약)
  - [기존 프로젝트에 최초 버전 적용](#기존-프로젝트에-최초-버전-적용)
  - [운영 시 알아둘 점](#운영-시-알아둘-점)
- [2. 프로젝트별 코드 연결 위치](#2-프로젝트별-코드-연결-위치)
- [3. Python: pyproject.toml](#3-python-pyprojecttoml)
- [4. Node.js: package.json과 npm 잠금 파일](#4-nodejs-packagejson과-npm-잠금-파일)
- [5. Spring Boot: Gradle Groovy DSL](#5-spring-boot-gradle-groovy-dsl)
- [6. Kotlin: Gradle Kotlin DSL](#6-kotlin-gradle-kotlin-dsl)
- [7. 버전 파일 변경을 저장소에도 남기려면](#7-버전-파일-변경을-저장소에도-남기려면)
- [8. 적용 범위와 검증](#8-적용-범위와-검증)

## 1. release.yml 동작 요약

| 항목 | 동작 |
|---|---|
| 실행 조건 | `main` 브랜치 push, PR 병합으로 발생한 push 포함 |
| 판별 대상 | 해당 push의 마지막 커밋인 `HEAD`의 제목 |
| 기준 버전 | 저장소 전체의 `vMAJOR.MINOR.PATCH` 태그 중 숫자상 가장 큰 버전 |
| 태그가 없을 때 | 커밋 접두사와 관계없이 `v1.0.0` 생성 |
| 중복 방지 | 현재 커밋의 태그를 재사용하며, Release가 없으면 생성하고 있으면 유지 |
| 권한 | 기본 `GITHUB_TOKEN`과 `contents: write` 사용 |
| 생성 결과 | 경량 Git 태그와 자동 릴리스 노트가 포함된 정식 GitHub Release |
| 실행 결과 확인 | GitHub Actions 실행 요약 |

현재 버전이 `v1.2.3`인 경우:

| 커밋 제목 예시 | 새 태그 | 계산 규칙 |
|---|---|---|
| `major: 호환되지 않는 API 변경` | `v2.0.0` | major + 1, minor/patch = 0 |
| `minor: 검색 기능 추가` | `v1.3.0` | minor + 1, patch = 0 |
| `patch: 검색 오류 수정` | `v1.2.4` | patch + 1 |
| `feat: 검색 기능 추가` | 생성하지 않음 | 지원하지 않는 접두사 |
| `fix: 검색 오류 수정` | 생성하지 않음 | 지원하지 않는 접두사 |
| `Major: API 변경` | 생성하지 않음 | 대소문자가 다름 |
| `문서 수정` | 생성하지 않음 | 접두사 없음 |

정식 버전 태그가 없는 상태에서 main에 처음 push하면 커밋 제목과 관계없이 `v1.0.0` 태그와 Release를 생성합니다. 이후부터 위 접두사 규칙을 적용합니다. `init:`는 버전이 없는 기존 프로젝트를 명시적으로 초기화하는 접두사이며, 정식 버전이 이미 있으면 초기화를 건너뜁니다. 최초 여부는 브랜치 생성 이벤트나 커밋 수가 아니라 정식 버전 태그의 부재로 판별합니다. 기존 저장소에 워크플로를 도입한 경우도 같으며, 기존 태그가 있으면 초기화하지 않습니다.

접두사는 제목 맨 앞에 있어야 하며 콜론 뒤 공백은 선택 사항입니다. 커밋 본문은 판별하지 않습니다. 여러 커밋을 한 번에 push해도 마지막 제목만 확인하므로 앞선 커밋의 `major:`는 반영되지 않습니다. PR 병합 시에는 최종 merge/squash 커밋 제목에 원하는 접두사가 있어야 합니다.

현재 워크플로는 GitHub CLI의 `gh release create --verify-tag --generate-notes`로 정식 Release를 게시합니다. 제목은 버전 태그이며 본문은 자동 생성됩니다. 빌드 산출물은 첨부하지 않습니다. 프로젝트 버전 파일 수정, 빌드, 애플리케이션 배포는 수행하지 않습니다. 태그 push 후 Release 생성이 실패하면 같은 실행을 재실행하여 복구할 수 있습니다. 기존 Release는 덮어쓰지 않습니다. [GitHub CLI 문서](https://cli.github.com/manual/gh_release_create)

### 기존 프로젝트에 최초 버전 적용

이미 GitHub에 코드가 올라가 있지만 정식 버전 태그가 없다면, `release.yml`을 main에 반영한 뒤 다음과 같이 `init:` 커밋을 push합니다. 변경 파일이 없어도 빈 커밋으로 실행할 수 있습니다.

```bash
git switch main
git pull --ff-only origin main
git commit --allow-empty -m "init: 기존 프로젝트 버전 관리 시작"
git push origin main
```

`init:` 커밋에 `v1.0.0` 태그와 GitHub Release가 생성됩니다. 이미 정식 버전 태그가 있다면 새 초기화 커밋은 버전을 변경하지 않습니다. 같은 태그 대상 커밋의 재실행은 기존 태그를 재사용하고 누락된 Release를 복구합니다. 접두사 없는 최초 자동 초기화도 유지하므로 워크플로를 처음 추가한 push에서 이미 `v1.0.0`이 생성되었다면 추가 `init:` 커밋은 필요하지 않습니다.

### 운영 시 알아둘 점

- `v1.2.3-beta`나 `v1.2.3+build` 같은 태그는 기준 버전에서 제외합니다.
- 기준 태그는 브랜치별로 분리하지 않습니다. MSA 저장소에서 서비스별 독립 버전이 필요하면 태그 이름과 검색 범위를 서비스별로 설계해야 합니다.
- 동시 실행 그룹으로 태그 생성 작업을 직렬화합니다. 실행 순서는 보장되지 않으며 push가 몰리면 대기 중이던 실행이 대체될 수 있습니다.
- 저장소 또는 조직의 태그 제한 정책이 있으면 `contents: write`가 있어도 push가 거부될 수 있습니다.
- 기본 `GITHUB_TOKEN`의 태그 push로는 일반적인 후속 push 워크플로가 실행되지 않습니다. 빌드가 필요하면 같은 워크플로 안에서 연결합니다.
- `fetch-depth: 0`은 전체 이력을 가져오므로 큰 저장소에서는 다운로드 시간이 늘어날 수 있습니다.

## 2. 프로젝트별 코드 연결 위치

모든 예제는 **Ubuntu/Bash, 저장소 루트의 단일 프로젝트**를 전제로 합니다. 해당 프로젝트에서 사용하는 Python, Node.js/npm, JDK 및 Gradle Wrapper를 먼저 준비해야 합니다. 실제 빌드는 프로젝트에서 정한 Docker 빌드 환경에서 실행하고 필요한 파일과 버전 값을 컨테이너에 전달하세요.

현재 `release.yml`에서 최초 버전/접두사 분기가 끝나는 `fi` 다음, 새 태그를 만드는 `git tag "$next_tag" HEAD` 바로 전에 아래 공통 코드와 해당 프로젝트의 갱신 코드를 넣습니다. 최초 릴리스에서는 모든 제목에 갱신 코드를 실행하며, 이후 지원하지 않는 접두사는 앞선 `exit 0`에서 종료합니다. 이미 태그가 있는 재실행에서는 갱신 코드를 건너뛰고 Release만 확인합니다.

```bash
# next_tag는 기존 case문에서 계산됩니다. 예: v1.3.0
# 프로젝트 메타데이터에는 접두사 v를 제거한 1.3.0을 사용합니다.
export RELEASE_VERSION="${next_tag#v}"
```

실행 순서는 `버전 계산 → RELEASE_VERSION 설정 → 프로젝트 버전 갱신 → 필요한 검증/빌드 → 기존 태그 생성 및 push → GitHub Release 게시`입니다. 각 도구에서 `minor` 등을 다시 계산하지 말고, 태그 기준으로 계산한 정확한 버전을 전달합니다.

아래 Bash 코드는 기존 `run: |` 안에 넣는 코드입니다. Python heredoc 본문과 마지막 `PY`까지 기존 셸 코드와 동일한 YAML 기본 들여쓰기를 적용해야 합니다. `RELEASE_VERSION`은 같은 step의 셸에서만 유지되므로 별도 step으로 분리한다면 `$GITHUB_ENV` 또는 step output으로 전달하고, 버전업 생략 시 후속 step도 건너뛰게 해야 합니다.

## 3. Python: pyproject.toml

`[project].version`에 정적 버전을 두는 프로젝트 예제입니다.

```toml
[project]
name = "sample-service"
version = "1.2.3"
```

TOML의 주석과 기존 서식을 유지하면서 특정 키만 수정하기 위해 `tomlkit`을 사용합니다. 이는 예제 적용 시 필요한 **릴리스 도구용 의존성**이며, 현재 저장소에 설치하거나 런타임 의존성으로 추가한 것은 아닙니다. 운영 환경에서는 검증한 버전을 릴리스 도구용 requirements/lock 파일에 고정하여 준비하세요. [TOML Kit 문서](https://tomlkit.readthedocs.io/en/latest/)

갱신 코드 실행 전에 도구를 준비하는 명령:

```bash
python -m pip install tomlkit
```

버전 갱신 코드:

```bash
python - <<'PY'
import os
import re
from pathlib import Path

import tomlkit

releaseVersion = os.environ["RELEASE_VERSION"]
if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", releaseVersion):
    raise SystemExit("RELEASE_VERSION 형식이 올바르지 않습니다.")

projectPath = Path("pyproject.toml")
document = tomlkit.parse(projectPath.read_text(encoding="utf-8"))
project = document.get("project")
if project is None:
    raise SystemExit("[project] 테이블이 필요합니다.")
if "version" in project.get("dynamic", []):
    raise SystemExit("동적 버전 프로젝트는 해당 빌드 도구의 버전 공급원을 수정해야 합니다.")
if "version" not in project:
    raise SystemExit("[project].version 값이 필요합니다.")

project["version"] = releaseVersion
projectPath.write_text(tomlkit.dumps(document), encoding="utf-8")
print(f"Python 버전: {releaseVersion}")
PY
```

이 예제는 `[tool.poetry].version`, `setup.py`, `__version__`를 수정하지 않습니다. `dynamic = ["version"]` 또는 Git 태그 기반 버전 도구를 사용하는 프로젝트에는 그대로 적용하지 마세요. Python 패키지 버전은 정적 값과 동적 공급원 중 프로젝트가 채택한 방식을 따라야 합니다. [Python 패키징 문서](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)

수정 후에는 기존 프로젝트의 테스트와 패키지 빌드를 수행합니다. uv/Poetry 등 잠금 파일에 프로젝트 버전이 들어 있는 구성이면 해당 도구로 잠금 파일도 동기화해야 합니다.

## 4. Node.js: package.json과 npm 잠금 파일

npm을 사용하는 단일 패키지 프로젝트 예제입니다.

```json
{
  "name": "sample-service",
  "version": "1.2.3",
  "private": true
}
```

버전 갱신 코드:

```bash
npm version "$RELEASE_VERSION" \
  --no-git-tag-version \
  --ignore-scripts \
  --allow-same-version
```

`package.json`과 존재하는 npm 잠금 파일의 프로젝트 버전을 갱신합니다. `--no-git-tag-version`으로 npm의 커밋/태그 생성을 막아 기존 워크플로가 태그를 생성하게 합니다. `--ignore-scripts`는 버전 변경 lifecycle script를 실행하지 않으며, `--allow-same-version`은 파일에 이미 같은 버전이 있어도 허용합니다. [npm version 문서](https://docs.npmjs.com/cli/v11/commands/npm-version/)

잠금 파일이 있는 프로젝트에서는 이후 `npm ci`와 프로젝트의 테스트/빌드를 수행할 수 있습니다. 이 코드는 의존성 버전을 올리지 않습니다. pnpm/Yarn 잠금 파일이나 npm workspaces 전체를 일괄 갱신하는 예제가 아니므로 해당 구성에는 별도 적용이 필요합니다.

## 5. Spring Boot: Gradle Groovy DSL

Java 17+와 Gradle 기반 Spring Boot 프로젝트를 기준으로 합니다. 애플리케이션 버전과 Spring Boot 플러그인/의존성 버전은 별개이며, 여기서는 **애플리케이션 버전만** 변경합니다.

저장소 루트 `gradle.properties`에 아래 키를 한 번 추가합니다. 다른 설정은 유지합니다.

```properties
releaseVersion=1.2.3
```

`build.gradle`의 기존 고정 `version = '...'` 선언을 다음 선언으로 교체합니다. 별도의 플러그인을 추가할 필요는 없습니다.

```groovy
version = providers.gradleProperty('releaseVersion').get()
```

버전 갱신 코드는 다음과 같습니다. `releaseVersion=...` 형식의 단일 행만 수정하고, 키가 없거나 중복이면 실패하도록 합니다.

```bash
python - <<'PY'
import os
import re
from pathlib import Path

releaseVersion = os.environ["RELEASE_VERSION"]
if not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", releaseVersion):
    raise SystemExit("RELEASE_VERSION 형식이 올바르지 않습니다.")

propertiesPath = Path("gradle.properties")
with propertiesPath.open(encoding="utf-8", newline="") as source:
    content = source.read()

updatedContent, count = re.subn(
    r"(?m)^([ \t]*releaseVersion[ \t]*=)[^\r\n]*",
    lambda match: f"{match.group(1)}{releaseVersion}",
    content,
)
if count != 1:
    raise SystemExit("gradle.properties에 releaseVersion=... 행이 정확히 하나 있어야 합니다.")

with propertiesPath.open("w", encoding="utf-8", newline="") as target:
    target.write(updatedContent)
print(f"Gradle 프로젝트 버전: {releaseVersion}")
PY
```

이 스크립트는 Python 표준 라이브러리만 사용합니다. 파일 수정 후 프로젝트 빌드 환경에서 `./gradlew test bootJar`로 테스트와 실행 JAR 생성을 수행할 수 있습니다. 기본 아카이브 설정에서는 프로젝트 버전이 JAR 이름에 반영되지만, 파일명을 따로 지정한 프로젝트는 그 설정을 따릅니다.

파일을 수정하지 않고 해당 빌드에만 버전을 주입하려면 같은 `build.gradle` 설정에서 다음 방식을 사용할 수도 있습니다. 두 방식 중 필요한 하나를 선택합니다.

```bash
./gradlew -PreleaseVersion="$RELEASE_VERSION" test bootJar
```

`-P`로 전달한 프로젝트 속성은 파일의 기본값보다 우선합니다. [Gradle 프로젝트 속성 문서](https://docs.gradle.org/current/userguide/project_properties.html)

## 6. Kotlin: Gradle Kotlin DSL

Kotlin/JVM 프로젝트도 Gradle의 프로젝트 버전을 사용합니다. Kotlin 컴파일러나 Kotlin 플러그인 버전을 변경하는 작업은 아닙니다.

루트 `gradle.properties`:

```properties
releaseVersion=1.2.3
```

`build.gradle.kts`의 기존 고정 버전 선언을 교체합니다.

```kotlin
version = providers.gradleProperty("releaseVersion").get()
```

**버전 파일 갱신 코드는 5절의 Python 스크립트를 그대로 사용합니다.** 대상 파일과 키가 동일하므로 Groovy DSL/Kotlin DSL에 따라 갱신 스크립트를 나눌 필요는 없습니다. 갱신 후 일반 Kotlin/JVM 프로젝트는 `./gradlew build`, Kotlin Spring Boot 프로젝트는 `./gradlew test bootJar`를 사용합니다.

파일 수정 없이 빌드에만 주입하는 대안:

```bash
# 일반 Kotlin/JVM 프로젝트
./gradlew -PreleaseVersion="$RELEASE_VERSION" build

# Kotlin + Spring Boot 프로젝트에서는 위 명령 대신 사용
./gradlew -PreleaseVersion="$RELEASE_VERSION" test bootJar
```

멀티 모듈 프로젝트에서는 배포하는 각 모듈에도 `version` 설정이 적용되어야 합니다. 루트의 버전을 설정했다고 모든 하위 모듈에 자동으로 같은 버전이 적용되는 것은 아닙니다. Android의 `versionCode`/`versionName`은 이 예제의 대상이 아닙니다. [Gradle JVM 빌드 문서](https://docs.gradle.org/current/userguide/building_java_projects.html)

## 7. 버전 파일 변경을 저장소에도 남기려면

위 예제를 기존 `run`에 삽입하면 **runner 작업 디렉터리의 파일만 변경**됩니다. 기존 `git tag "$next_tag" HEAD`는 원래 커밋을 가리키므로 미커밋 파일 변경을 태그에 포함하지 않습니다. 따라서 해당 태그를 나중에 checkout하면 원래 버전 파일을 보게 됩니다.

빌드용 버전 주입이 목적이면 변경된 작업 디렉터리에서 산출물을 만들고, 재빌드할 때도 태그에서 버전을 다시 주입하는 방식으로 사용할 수 있습니다.

버전 파일 자체를 저장소와 태그에 보존하려면 별도의 릴리스 커밋 흐름이 필요합니다.

1. 접두사로 버전을 계산하고 해당 프로젝트의 버전 파일과 잠금 파일을 갱신합니다.
2. 테스트/빌드로 검증합니다.
3. 변경된 버전 파일만 명시적으로 stage하고 `chore: release v1.3.0` 같은 커밋을 생성합니다.
4. **새 릴리스 커밋**에 태그를 붙이고 브랜치와 태그를 함께 push하도록 워크플로를 변경합니다.

이 방식은 현재 구현에 포함되어 있지 않습니다. 적용 시 브랜치 보호 규칙, checkout의 detached HEAD, 실행 중 추가 push로 인한 non-fast-forward, 원본 push 커밋을 재실행할 때의 중복 감지를 함께 설계해야 합니다. 브랜치 보호가 있는 저장소에서는 버전 변경 PR을 사용하는 흐름도 고려할 수 있습니다.

## 8. 적용 범위와 검증

| 프로젝트 | 버전 값의 위치 | 추가 도구/설정 |
|---|---|---|
| Python | `pyproject.toml`의 `[project].version` | Python + 릴리스용 `tomlkit` |
| Node.js | `package.json`, npm 잠금 파일 | Node.js + npm |
| Spring Boot | `gradle.properties`의 `releaseVersion` | Python, JDK, Gradle Wrapper, Groovy DSL 연결 |
| Kotlin/JVM | `gradle.properties`의 `releaseVersion` | Python, JDK, Gradle Wrapper, Kotlin DSL 연결 |

실제 프로젝트에 적용할 때는 `major:`, `minor:`, `patch:`, 그 외 제목의 네 가지 경우를 확인하고, 산출물의 버전이 계산한 태그와 일치하는지 검증하세요. 현재 폴더에는 각 언어의 실제 프로젝트가 없으므로 프로젝트별 빌드와 GitHub Actions 원격 실행은 별도로 검증해야 합니다.
