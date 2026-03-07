#!/bin/bash
set -euo pipefail
docker port "$1" 8001 | head -n 1 | cut -d: -f2
