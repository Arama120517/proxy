#!/bin/sh
wget -q http://127.0.0.1:8299/download/sub?target=sing-box -O output/subs-check-results.json
pkill -9 -f subs-check