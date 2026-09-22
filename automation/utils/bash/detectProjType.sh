if [ "$TYPE" = "auto" ]; then
  FOUND=()

  [ -f "build.gradle" ] && FOUND+=("gradle")
  [ -f "pom.xml" ] && FOUND+=("maven")
  [ -f "package.json" ] && FOUND+=("node")
  [ -f "pyproject.toml" ] && FOUND+=("python")

  if [ "${#FOUND[@]}" -eq 0 ]; then
    echo "지원하는 버전 파일을 찾지 못했습니다."
    exit 1
  fi

  if [ "${#FOUND[@]}" -gt 1 ]; then
    echo "여러 프로젝트 파일이 발견되었습니다:"
    printf ' - %s\n' "${FOUND[@]}"
    echo "workflow_dispatch에서 project_type을 직접 선택하세요."
    exit 1
  fi

  TYPE="${FOUND[0]}"
fi

case "$TYPE" in
  gradle)
    FILE="build.gradle"
    ;;
  maven)
    FILE="pom.xml"
    ;;
  node)
    FILE="package.json"
    ;;
  python)
    FILE="pyproject.toml"
    ;;
  *)
    echo "지원하지 않는 project_type: $TYPE"
    exit 1
    ;;
esac

if [ ! -f "$FILE" ]; then
  echo "$FILE 파일이 없습니다."
  exit 1
fi

echo "type=$TYPE" >> "$GITHUB_OUTPUT"
echo "file=$FILE" >> "$GITHUB_OUTPUT"

echo "Project type: $TYPE"
echo "Version file: $FILE"