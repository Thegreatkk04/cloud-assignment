#!/usr/bin/env bash
# Task 2 step 6: score base, student and (if present) teacher outputs.
set -euo pipefail
mkdir -p results
python training/predict.py --model EleutherAI/pythia-70m --out results/pred_base.jsonl
python tools/score.py results/pred_base.jsonl data/validation.jsonl --out results/score_base.json | tee results/score_base.txt
if [ -d models/v1 ]; then
  python training/predict.py --model models/v1 --out results/pred_student_v1.jsonl
  python tools/score.py results/pred_student_v1.jsonl data/validation.jsonl --out results/score_student_v1.json | tee results/score_student_v1.txt
fi
if [ -f results/pred_teacher.jsonl ]; then
  python tools/score.py results/pred_teacher.jsonl data/validation.jsonl --out results/teacher_validation.json | tee results/teacher_validation.txt
fi
