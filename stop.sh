#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$DIR/.server.pid"

if [ -f "$PID_FILE" ]; then
  pid=$(cat "$PID_FILE")
  if kill "$pid" 2>/dev/null; then
    echo "已停止 (PID $pid)"
    rm "$PID_FILE"
  else
    echo "Server 不在運作中"
    rm -f "$PID_FILE"
  fi
else
  echo "找不到 PID，嘗試用 port 找..."
  pid=$(lsof -ti tcp:3001)
  if [ -n "$pid" ]; then
    kill "$pid" && echo "已停止 (PID $pid)"
  else
    echo "Port 3001 沒有在使用"
  fi
fi
