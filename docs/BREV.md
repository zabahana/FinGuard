# Run FinGuard on NVIDIA Brev

The current simulation runs on Linux with Python 3.10 or newer. It does not require or exercise a GPU. Use an existing instance or a CPU instance for this milestone. Select GPU hardware when adding a local model and size it against the model's memory requirements.

## Connect and run

Create or select an instance in the [Brev console](https://brev.nvidia.com/) and use its connection instructions to open a shell. The Mac does not need Homebrew when you use the console connection workflow. See the [NVIDIA quickstart](https://docs.nvidia.com/brev/getting-started/quickstart).

Run these commands on the instance:

```sh
git clone https://github.com/zabahana/FinGuard.git
cd FinGuard
bash scripts/setup-brev.sh
```

If the repository is private, authenticate Git on the instance using your GitHub account. Do not place tokens in clone URLs or project files. If already cloned, enter the checkout and run `git pull --ff-only` before the setup script.

The script creates a local virtual environment, installs the optional API and test client, runs the tests and investigation, then evaluates 1,000 scenario replays per mode. Reports are written to a new directory under `artifacts/brev/` each run. The setup requires package-download network access. If Python reports that venv/ensurepip is unavailable on Ubuntu, install the matching `python3-venv` system package first.

## Optional API

```sh
.venv/bin/python -m uvicorn finguard.api:app --host 127.0.0.1 --port 8000
```

Keep the API bound to loopback and access it over an SSH tunnel. In another terminal on your computer, using the instance's configured SSH alias:

```sh
ssh -L 8000:127.0.0.1:8000 YOUR_INSTANCE_SSH_ALIAS
```

Then open `http://127.0.0.1:8000/docs` on your computer. The synthetic API has no authentication; do not expose it as a public endpoint.

## What this validates

This run validates the Python testbed on the remote instance. It does not measure OpenShell containment, model behavior, or GPU performance. See [the OpenShell integration plan](OPENSHELL.md) for that milestone. No instance provisioning or paid-resource creation is performed by the setup script.
