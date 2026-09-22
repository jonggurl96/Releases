# GitHub Actions 릴리스 워크플로 예제

이 저장소에는 두 가지 릴리스 워크플로 예제가 있습니다. 현재 `.github/workflows/` 디렉터리가 없으므로, 원하는 프로젝트에 설치해야 실행됩니다. 애플리케이션 소스와 빌드 설정은 포함하지 않습니다.

| 방식 | 파일 | 실행 조건 | 결과 |
| --- | --- | --- | --- |
| 커밋 접두사 | [`prefix/release.yml`](prefix/release.yml) | `main` push | 현재 커밋에 버전 태그와 GitHub Release 생성 |
| 수동 버전 갱신 | [`automation/release.yml`](automation/release.yml) | Actions의 수동 실행 | 버전 파일 수정 커밋, 태그, GitHub Release 생성 |

두 방식 모두 `contents: write` 권한의 기본 `GITHUB_TOKEN`을 사용합니다. 빌드 산출물 첨부나 배포는 구현되어 있지 않습니다.

## 커밋 접두사 방식

`prefix/release.yml`을 대상 저장소의 `.github/workflows/release.yml`로 복사합니다. 기본 대상 브랜치는 `main`입니다.

정식 `vMAJOR.MINOR.PATCH` 태그가 없다면 첫 push의 커밋 제목과 관계없이 `v1.0.0`을 만듭니다. 이후에는 push 대상의 마지막 커밋 제목 맨 앞을 확인합니다. 접두사는 대소문자를 구분하며 콜론 뒤 공백은 선택 사항입니다.

| 현재 태그 | 커밋 제목 | 결과 |
| --- | --- | --- |
| `v1.2.3` | `major: API 변경` | `v2.0.0` |
| `v1.2.3` | `minor: 기능 추가` | `v1.3.0` |
| `v1.2.3` | `patch: 버그 수정` | `v1.2.4` |
| `v1.2.3` | `feat: 기능 추가` | 생성하지 않음 |

`init:`는 정식 버전 태그가 없을 때 `v1.0.0`을 명시적으로 초기화합니다. 기존 정식 태그가 있으면 종료합니다. 기준 버전은 브랜치와 무관하게 저장소 전체의 정식 버전 태그 중 숫자상 가장 큰 값입니다. `v1.2.3-beta` 등은 제외합니다. 여러 커밋을 push하거나 PR을 병합하면 마지막 merge 또는 squash 커밋의 제목만 검사합니다.

워크플로는 해당 커밋에 경량 태그를 붙입니다. 버전 파일과 브랜치 커밋은 수정하지 않습니다. 같은 커밋에서 재실행하면 태그를 재사용하고 누락된 Release를 생성합니다. 기존 Release는 유지합니다. 결과는 Actions 실행 요약에 기록됩니다.

## 수동 버전 갱신 방식

`automation/release.yml`은 `workflow_dispatch`로 실행하는 단일 프로젝트 예제입니다.

1. `automation/release.yml`을 대상 프로젝트의 `.github/workflows/release.yml`로 복사합니다.
2. `automation/utils/bash/` 및 `automation/utils/python/`의 파일을 각각 `.github/workflows/utils/bash/`, `.github/workflows/utils/python/`로 복사합니다.
3. Actions의 **Run workflow**에서 `project_type`(`auto`, `gradle`, `maven`, `node`, `python`, `flutter`)과 `bump`(`patch`, `minor`, `major`)를 선택합니다.

`auto`는 루트의 `build.gradle`, `pom.xml`, `package.json`, `pyproject.toml`, `pubspec.yaml`을 찾습니다. 파일이 없거나 둘 이상이면 실패합니다. 여러 종류가 있는 프로젝트는 타입을 명시해야 합니다.

| 타입 | 읽는 버전 | 갱신 방법 |
| --- | --- | --- |
| `gradle` | `build.gradle`의 문자열 리터럴 `version` | 첫 번째 일치 선언 수정 |
| `maven` | `pom.xml`의 최상위 `project.version` | Maven Versions Plugin 2.19.1 실행 |
| `node` | `package.json`의 `version` | `npm version --no-git-tag-version --ignore-scripts` |
| `python` | `pyproject.toml`의 `[project].version`, 없으면 `[tool.poetry].version` | 해당 섹션의 버전 행 수정 |
| `flutter` | `pubspec.yaml`의 최상위 `version` | 앱 버전 증가와 빌드 번호 1 증가 |

현재 버전의 앞부분 `MAJOR.MINOR.PATCH`를 읽어 선택한 단위를 증가시킵니다. 예를 들어 `1.2.3-SNAPSHOT`에서 `minor`를 선택하면 `1.3.0`과 태그 `v1.3.0`을 만듭니다. 이미 같은 태그가 있으면 실패합니다.

Flutter에서는 `version: 1.2.3+4`에 `minor`를 적용하면 `version: 1.3.0+5`로 수정하고 태그는 `v1.3.0`으로 만듭니다. 빌드 번호가 없다면 `+1`을 추가합니다. 최상위 `version`이 없거나 여러 개이거나 지원하지 않는 형식이면 실패합니다. 버전 행의 따옴표와 주석은 유지합니다. 이 단계는 Flutter SDK를 설치하거나 앱을 빌드하지 않습니다.

변경 사항은 `git add -A`로 모두 stage한 뒤 `chore(release): v...` 커밋과 annotated 태그를 만들고, 실행한 브랜치와 태그를 push합니다. 마지막에 자동 릴리스 노트가 담긴 GitHub Release를 게시합니다. 테스트 및 빌드 단계는 없습니다.

### 적용 시 확인할 사항

- 현재 예제의 경로 및 Bash 입력 전달 문제는 위 설치 단계에서 수정해야 합니다.
- Gradle은 `build.gradle`의 문자열 리터럴만 지원합니다. `build.gradle.kts` 및 `gradle.properties` 기반 버전은 지원하지 않습니다.
- Maven은 실행 가능한 `./mvnw`가 있으면 이를 사용하고, 없으면 `mvn`을 사용합니다. Node 단계는 Node 24를 설정하며 Python 스크립트는 Python 3 표준 라이브러리를 사용합니다.
- `git add -A`는 버전 파일 외의 변경도 커밋할 수 있습니다. 대상 프로젝트에 맞게 stage 대상을 제한하고 브랜치 보호 규칙 및 토큰의 push 권한을 확인하세요.
