#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$DIR/.server.pid"

# 載入環境變數
if [ -f "$DIR/.env" ]; then
  set -a; source "$DIR/.env"; set +a
else
  echo "⚠️  找不到 .env 檔，請參考 .env.example 建立"
  exit 1
fi

if [ -f "$PID_FILE" ]; then
  pid=$(cat "$PID_FILE")
  if kill -0 "$pid" 2>/dev/null; then
    echo "已在運作中 (PID $pid)  →  http://localhost:3001"
    open http://localhost:3001
    exit 0
  fi
fi

# 確認依賴已安裝
if ! /usr/bin/python3 -c "import yfinance, flask, supabase" 2>/dev/null; then
  echo "安裝依賴套件..."
  /usr/bin/python3 -m pip install -r "$DIR/requirements.txt" -q
fi

nohup /usr/bin/python3 "$DIR/server.py" \
  > /tmp/twse-map.log 2>&1 &
echo $! > "$PID_FILE"
echo "啟動完成 (PID $!)  →  http://localhost:3001"
sleep 0.8
open http://localhost:3001
