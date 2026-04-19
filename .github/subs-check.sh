#!/bin/bash

wget -q http://127.0.0.1:8299/download/sub?target=sing-box -O results.json

pkill -9 -f subs-check
curl -sL http://127.0.0.1:3000/exit