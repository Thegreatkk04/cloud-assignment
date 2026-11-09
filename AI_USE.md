# AI use in this project

Tool used: Claude (Anthropic), in chat, on 9 November 2026.

What I used it for:
- Writing the first draft of most source files after I explained each task: the labelling worker, clean.py, train.py and predict.py, the FastAPI service, the Kubernetes manifests, the Makefile and shell scripts, the unit tests and the CI workflow.
- Working out the subnet table (I checked the arithmetic by hand: 2^10 - 2 = 1022, 2^8 - 2 = 254, 2^7 - 2 = 126, 2^5 - 2 = 30).
- Help with the wording of the report.

How I checked what it gave me:
- Every script that could be run without the cluster was run: nacl_sim.py (6/6), subnet_calc.py, pyflakes, pytest (13 tests), predict.py + score.py for the untrained base model, cost.py. The outputs are in results/.
- Two of the generated unit tests had wrong expectations at first (a float comparison that was too strict, and a NACL test that expected a deny for a packet the rules correctly allow as reply traffic). I fixed the tests, not the code, after reading the rules again.
- The parts that need the cluster, Ollama or hours of CPU training were not executed before the deadline. The report says so in each section. No numbers were invented for those parts.
