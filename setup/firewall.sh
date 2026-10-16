#!/usr/bin/env bash
# setup/firewall.sh — ufw 활성 시에만 20000/tcp 허용(멱등). 아니면 no-op.
set -euo pipefail
command -v ufw >/dev/null 2>&1 || {
  echo "ufw 없음 — 스킵"
  exit 0
}
ufw status 2>/dev/null | grep -q "Status: active" || {
  echo "ufw 비활성 — 스킵"
  exit 0
}
sudo ufw allow 20000/tcp comment 'dayboard'
echo "Firewall 규칙 반영(ufw)."
