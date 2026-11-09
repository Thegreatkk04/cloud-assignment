.PHONY: up down deploy label clean-data train train-v2 eval lint test load cost

up:            ## cluster + storage + images + deploy (needs .env)
	bash scripts/up.sh
down:          ## delete the cluster
	k3d cluster delete cloud-mini
deploy:
	bash scripts/deploy.sh
label:         ## two teacher workers in namespace pipeline
	kubectl apply -f k8s/worker-job.yaml
	kubectl -n pipeline wait --for=condition=complete job/teacher-label --timeout=6h
clean-data:
	S3_ENDPOINT=http://localhost:8333 python worker/clean.py
train:         ## make train  |  make train SUBSET=50
	python training/train.py $(if $(SUBSET),--subset $(SUBSET),)
train-v2:
	python training/train.py --seed 7 --out models/v2
eval:
	bash scripts/evaluate.sh
lint:
	python -m pyflakes worker service training scripts tests
test:
	python -m pytest -q tests
load:
	locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/loadtest
cost:          ## make cost RPS=1.5
	python scripts/cost.py --replicas 2 --cpu-limit 1 --mem-gib 1 --rps $(RPS)
