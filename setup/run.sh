#!/usr/bin/env bash
# setup/run.sh — dayboard 기동. server-manager·systemd·직접 호출 공통 SSOT.
# venv 인터프리터 직접 사용(런타임 PATH/uv 비의존) → systemd robust.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
exec "$root/.venv/bin/python" -u -m dayboard.serve
