#!/usr/bin/env bash
# Run the two labelling workers on the laptop (no cluster) against a local Ollama.
set -euo pipefail
mkdir -p datasets/teacher
for i in 0 1; do
  SHARD_INDEX=$i SHARD_COUNT=2 OLLAMA_URL=http://localhost:11434 \
  LOCAL_POOL=data/commands_pool.jsonl LOCAL_OUT=datasets/teacher python worker/label_worker.py &
done
wait
python worker/clean.py --local-shards datasets/teacher --local-out datasets/v1
