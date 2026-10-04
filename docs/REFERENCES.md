# Sources and references

## Data and models

- [ULB and Worldline credit-card fraud dataset on Kaggle](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud): the original anonymized transaction data and labels. FinGuard's deduplication, chronological split, threshold selection, and reported metrics are project-specific experiments, documented in the [dataset methodology](https://github.com/zabahana/FinGuard/blob/main/docs/ULB.md).
- [Qwen3 8B model card](https://huggingface.co/Qwen/Qwen3-8B) and [Ollama qwen3:8b distribution](https://ollama.com/library/qwen3:8b): the pretrained language model and the packaged model used for local inference. FinGuard does not train or fine-tune Qwen.
- [scikit-learn HistGradientBoostingClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html): the fraud detector implementation. [pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/), and [joblib](https://joblib.readthedocs.io/en/stable/) support data preparation, numerical operations, and local model persistence.

## Runtime security and inference

- [NVIDIA OpenShell 0.1.2 source and release](https://github.com/NVIDIA/OpenShell/releases/tag/v0.1.2): the pinned software runtime used by this implementation. The [NVIDIA platform announcement](https://nvidianews.nvidia.com/news/open-agent-safety-platform) supplies the broader Open Agent Safety Platform context; Sentry hardware is not part of this demo.
- [Ollama source code](https://github.com/ollama/ollama): the local inference server. [Docker Desktop documentation](https://docs.docker.com/desktop/): the container environment on the development Mac.
- [Open Cybersecurity Schema Framework](https://ocsf.io/): the schema framework used by the native security event export. OCSF is an event schema, not a certification of FinGuard or its security claims.

## Project code and publication tooling

- [FinGuard implementation](https://github.com/zabahana/FinGuard/tree/main/finguard), [OpenShell policies](https://github.com/zabahana/FinGuard/tree/main/integration/openshell), and [Attack Lab methodology](https://github.com/zabahana/FinGuard/blob/main/docs/ATTACK_LAB.md): the application controls, bounded adversarial harness, configuration, and experimental qualifications developed for this project.
- [Saved investigation snapshot](https://github.com/zabahana/FinGuard/blob/main/docs/visuals/snapshot.json) and [Attack Lab snapshot](https://github.com/zabahana/FinGuard/blob/main/docs/visuals/attack-lab-snapshot.json): the exported observations and source hashes behind the figures. These are local experiment results, not NVIDIA benchmark results or independent certification reports. Full runtime logs remain local and are not committed.
- [Mermaid](https://mermaid.js.org/), [Playwright](https://playwright.dev/), [Marked](https://marked.js.org/), and [Sharp](https://sharp.pixelplumbing.com/): diagram rendering, browser checks and screenshots, Markdown-to-HTML conversion, and figure image generation. Figure content and captions were authored for FinGuard.

Upstream projects retain their own licenses and dataset/model terms. The references identify dependencies and provenance; they do not imply endorsement by their authors.
