#!/usr/bin/env bash
# setup/install.sh — 1회 실행. uv가 .venv 생성 + Python 3.14 프로비저닝 + deps 설치.
# = server.toml [hooks] post_install (server-manager update가 재빌드에 호출).
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/.." && pwd)"
command -v uv >/dev/null || {
  echo "ERROR: 'uv' not found. curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
}
(cd "$root" && uv sync)
"$here/firewall.sh" || true
echo "Setup complete. Start with: setup/run.sh  (or: systemctl enable --now dayboard)"
