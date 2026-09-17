#!/bin/sh
set -e
cd /workspace
python3 course/build.py >/tmp/devops-build.log 2>&1 || true
if curl -sf http://127.0.0.1:8080/ >/dev/null 2>&1; then
  exit 0
fi
cd /workspace/docs
python3 -m http.server 8080 --bind 0.0.0.0 >/tmp/devops-pages.log 2>&1 &
sleep 0.4
exit 0
