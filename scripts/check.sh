#!/usr/bin/env bash
#
# The project's check: every gate over the whole tree, red on the first that
# fails. The runner runs it for every pull request and every push to main or
# production (.github/workflows/ci.yml); a hand run only diagnoses. Run it
# after staging: it reads tracked files. Read its exit code directly, never
# through a pipe.
#
#   scripts/check.sh
#
# Gates, in order, the cheap ones first:
#   lint         shellcheck over every tracked file whose first line is a bash or sh shebang
#   format       shfmt -i 2 -ci -d over the same files
#   exec-bits    a script with a shebang carries the execute bit
#   hooks        every hook case holds (scripts/check-hooks.py)
#   sync         uv sync --frozen: the locked environment, dev group included
#   ruff         uv run ruff format --check . and uv run ruff check .
#   pytest       uv run pytest -q
#
# It writes no gate record: scripts/publish.sh says so on one line when it
# moves production, and publishes on reachability alone.
set -euo pipefail
cd "$(dirname "$0")/.."

# A script is a tracked file whose first line is a bash, sh or dash shebang;
# zsh is not shellcheck's, and a shebang quoted inside a document does not
# count.
scripts=()
while IFS= read -r -d '' f; do
  if [[ $(head -n 1 -- "$f" 2>/dev/null | tr -d "\0") =~ ^#!(/[^[:space:]]*/|[[:space:]]*/usr/bin/env[[:space:]]+)(ba|da)?sh([[:space:]]|$) ]]; then scripts+=("$f"); fi
done < <(git ls-files -z | sort -z)
echo "shellcheck: ${#scripts[@]} scripts"
if [ "${#scripts[@]}" -gt 0 ]; then
  shellcheck --severity=warning "${scripts[@]}"
  echo "shfmt"
  shfmt -i 2 -ci -d "${scripts[@]}"
fi

echo "exec-bits"
python3 scripts/check-script-exec-bits.py

echo "hooks"
python3 scripts/check-hooks.py

echo "sync"
uv sync --frozen --quiet

echo "ruff"
uv run --quiet ruff format --check .
uv run --quiet ruff check .

echo "pytest"
uv run --quiet pytest -q

echo "green"
