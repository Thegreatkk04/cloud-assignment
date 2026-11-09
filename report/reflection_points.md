# Points for the handwritten reflection (3 pages, file name <roll_number>.pdf)

Write these in your own words by hand. Put your name, roll number and the GitHub link
(https://github.com/Thegreatkk04/cloud-assignment) at the top of page 1.

## What I learnt
- What knowledge distillation is: a small model (pythia-70m) learns from the outputs of a
  bigger one (phi3.5). Sequence-level means we train on the teacher's text, not its logits.
- Why logit distillation was not possible: Ollama gives text only, and the two models have
  different tokenizers.
- How object storage fits in: weights live in SeaweedFS (S3 API), not in the image or in git;
  the pod downloads them at start-up, which is why /readyz exists.
- Kubernetes pieces and why each exists: Deployment (replicas, rolling update), Service,
  Ingress (Traefik), HPA, liveness vs readiness probe, Secret for credentials.
- Subnetting by hand: smallest prefix that fits, 2^(32-prefix) - 2 usable hosts.
- A NACL is stateless, so reply traffic needs its own rules and rule order matters.
- CI as a quality gate: score.py --min-validity 95 fails the pipeline for a bad model.

## Challenges I faced
- Time. Teacher labelling of 3,000 commands and CPU training take hours; I started too late.
- Could not run the cluster experiments without a trained model in storage.
- Two of my unit tests had wrong expectations (float rounding; a NACL packet I expected to be
  denied was correctly allowed as reply traffic). Had to re-read the rules to see the test was wrong.
- Keeping measured numbers and assumptions apart in the report.

## How I handled them
- Ran everything that does not need the cluster and saved outputs in results/ (nacl 6/6,
  13 tests, lint, base model score 0%, cost formula).
- Wrote "not executed, design only" instead of guessing numbers.
- Fixed the tests, not the code, after checking the rules.

## Findings / observations
- The untrained pythia-70m gives 0% valid JSON; it outputs random text like `- name: "calendar"`.
  This shows why fine-tuning is needed and what the CI gate will catch.
- Inference of the untrained model took 0.80 s per command on 2 CPU threads.
- Modulo sharding is simple and gap-free but cannot rebalance a slow worker.
- The ephemeral-port rule in a NACL is wide open by nature; a stateful firewall would be tighter.

## What could have been done better
- Start the teacher run on day one and let it run overnight.
- Do a 50-record training smoke test early so the pipeline is proven.
- Build the Docker image early to confirm the 2 GB limit.
- Run the GitHub Actions workflow once with the base model to get the failed-gate link.

## Improvements I would make next
- Work-queue based labelling instead of static shards.
- More epochs or a bigger student if full_frame is low.
- Cache the model in a volume so pods are not blocked by storage outages.
- Measure real rps and redo the cost with `make cost RPS=<value>`.
