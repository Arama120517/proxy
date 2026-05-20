#!/bin/sh
fetch -q -o /app/output/subs-check-results.json "http://127.0.0.1:8299/download/sub?target=sing-box"
killall -9 subs-check