# Cloud Computing Mini Project (CS3081) - Command Parser

Sequence-level knowledge distillation of a command parser (phi3.5 teacher -> pythia-70m student),
served from a container on a local k3d Kubernetes cluster with SeaweedFS object storage.

**Student:** Kapil Kumar  **Roll number:** 230103040
**GitHub repo:** https://github.com/Thegreatkk04/cloud-assignment

Status (honest): the code, manifests, tests, network files and CI workflow are complete and the
parts that run without a cluster have been executed (results/). Teacher labelling, student training,
the Docker image and the cluster experiments were **not executed** before the deadline because of
time; the report marks those sections as "design only, not executed" and gives no numbers for them.

## What it does
```
POST /parse  {"text": "set an alarm for seven thirty am tomorrow"}
->  {"intent": "alarm_set", "date": "tomorrow", "time": "seven thirty am", "place": null}
```

## Layout
```
cluster/k3d.yaml              Task 1  cluster config
prompts/teacher_prompt.txt    Task 1  teacher prompt
worker/                       Task 1  label_worker.py (sharded), clean.py, storage.py, Dockerfile
training/                     Task 2  train.py, predict.py, config.yaml, loss.csv (after training)
service/                      Task 3  FastAPI app, model_runner.py, Dockerfile
k8s/                          Tasks 1,4  namespaces, seaweedfs, worker job, deployment, service, ingress, hpa
network/                      Task 5  subnets.md, nacl.json, packets_sample.jsonl
tests/                        Task 6  13 unit tests
.github/workflows/ci.yml      Task 6  lint -> tests -> evaluation from Release -> gate -> gitleaks
scripts/                      helpers: up.sh, deploy.sh, cost.py, subnet_calc.py, evaluate.sh ...
tools/, data/                 the provided student kit
results/                      command outputs and evidence
report/                       report.pdf
```

## Prerequisites
Docker, k3d, kubectl, Python 3.11, Ollama with `phi3.5` pulled, `make`, Locust (`pip install locust`).

## Build and deploy (three commands)
```bash
cp .env.example .env     # set your own S3 access key / secret
make up                  # k3d cluster + SeaweedFS + buckets + build images + deploy service
make train               # train the student (needs datasets/v1/train.jsonl from Task 1)
```

## Task by task
```bash
# Task 1
ollama serve                               # teacher on the laptop
make label                                 # indexed Job: 2 workers (SHARD_INDEX 0,1) in namespace pipeline
make clean-data                            # -> datasets/v1/train.jsonl + train.sha256, counts in results/clean_counts.json
# (without a cluster: bash scripts/run_workers_local.sh)

# Task 2
pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu && pip install -r training/requirements.txt
make train SUBSET=50                       # smoke test
make train                                 # models/v1 + models/v1.tar.gz + model.sha256
make train-v2                              # models/v2 (seed 7)
python scripts/upload_model.py models/v1   # to the models bucket
make eval                                  # base / student / teacher scores -> results/
# publish models/v1.tar.gz as a GitHub Release asset under tag model-v1 (do not commit it)

# Task 3
docker build -f service/Dockerfile -t cloud-mini/service:v1 .
docker run --rm -p 8000:8000 --cpus 1 --memory 1g -e MODEL_URI=s3://models/v1 -e MODEL_VERSION=v1 \
  -e S3_ENDPOINT=http://host.docker.internal:8333 -e MAX_NEW_TOKENS=64 \
  -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... cloud-mini/service:v1
curl -s localhost:8000/parse -H 'content-type: application/json' -d '{"text":"weather in london"}' -i
# FAULT_INJECT=1 -> HTTP 500 {"error":"invalid_model_output"}

# Task 4
make deploy
kubectl -n app get deploy,svc,ingress,hpa,pods
kubectl -n app set env deploy/parser MODEL_VERSION=v2 MODEL_URI=s3://models/v2   # rolling update
kubectl -n app rollout undo deploy/parser                                         # rollback

# Task 5 (no cluster needed)
python scripts/subnet_calc.py
python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check

# Task 6
make lint && make test

# Task 7
make load                                  # Locust standard command -> results/loadtest*
make cost RPS=<measured rps>
```

## Testing
`make test` runs the 13 unit tests (clean.py, output validation, service API incl. FAULT_INJECT, subnets, NACL, cost).

## Shutdown
```bash
make down                # k3d cluster delete cloud-mini
```
