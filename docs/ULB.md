# Real ULB/Worldline credit-card fraud data

FinGuard supports the [original ULB/Worldline dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud): 284,807 anonymized European card transactions from two days in September 2013, with 492 fraud labels. This is a historical research benchmark, not a live bank connection.

The raw CSV has `Time`, `V1` through `V28`, `Amount`, and `Class`. Time is elapsed seconds from the first transaction. V1–V28 are PCA components with undisclosed meanings. Customer IDs, merchants, devices, countries, complaints and currency are unavailable. FinGuard does not invent these fields. `ULB-235645` means the 235,645th data row in the original CSV, not a customer or bank-issued transaction ID.

## Run on this Mac

The dataset, trained detector and local Qwen model are already installed. From the repository root:

```sh
# Start Ollama in another terminal if it is not running:
sh scripts/serve-model.sh

# Investigate the highest-scoring held-out transaction:
.venv/bin/python -m finguard investigate-transaction

# Investigate a specific held-out source row:
.venv/bin/python -m finguard investigate-transaction --transaction-id ULB-235645 --output artifacts/ulb-example
```

Each run writes `report.json` and redacted `events.jsonl`. The default output directory is `artifacts/ulb-investigation`; rerunning replaces its previous report. Specify a different `--output` to retain separate investigations. `--model` selects another locally installed Ollama model. These commands require a detector already trained using the procedure below.

## Download and train again

```sh
.venv/bin/python -m pip install -e '.[fraud]'
.venv/bin/python scripts/download-ulb.py
.venv/bin/python -m finguard train-fraud
```

The download comes directly from Kaggle's public dataset endpoint. No credential was required for the verified download. If Kaggle changes access requirements, obtain the original CSV from the dataset page and save it at `.local/datasets/ulb/creditcard.csv`. The downloader and trainer verify SHA-256 `76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89`. A changed dataset must be inspected before updating that expected digest. Raw data and trained artifacts are ignored by Git. Consult the source dataset's terms before redistribution.

Training uses a scikit-learn histogram gradient-boosted tree classifier on the Mac CPU. Qwen inference runs separately through Ollama on the GPU. Qwen itself is not fine-tuned on the dataset.

The pipeline:

1. Validate the exact numeric schema, finite values, nonnegative amounts/time, and binary labels. Reject identical features with conflicting labels.
2. Remove 1,081 duplicate feature rows, retaining stable original-row IDs. The cleaned dataset has 283,726 transactions and 473 fraud labels.
3. Sort by time and partition approximately 60% training, 20% validation, 20% test. Keep equal timestamps in the same partition.
4. Train on the first partition only, using a fixed seed and fixed model configuration. No oversampling or additional PCA is performed. Early stopping is disabled to avoid implicit random validation splits.
5. Choose a threshold using validation labels, maximizing recall at precision of at least 90%. If unattainable, explicitly report the maximum-F1 fallback.
6. Freeze the threshold and measure the held-out test partition. Report average precision, ROC-AUC, precision, recall, and all four confusion counts. Average precision is the non-interpolated summary of the precision–recall curve, not trapezoidal PR area.

The threshold is a research operating point, not a bank-approved cost or intervention policy. The score is uncalibrated, particularly because training uses balanced class weights. Do not interpret 0.99 as a 99% fraud probability. No test-based tuning is performed.

## Evidence and enforcement

The transaction agent receives three tools for evidence: `read_policy`, `transaction_evidence` and `risk_score`. It must successfully call all three before `submit_case` can execute. Every action goes through a fresh, transaction-bound Runner session and the adaptive guard. Other transaction IDs, arbitrary files, label lookups and unknown tools are denied. The backend independently restricts access to the assigned transaction.

The agent backend loads only `model.joblib` and the checksum-verified `test_features.csv`. The feature store excludes `Class`. It never reads the raw CSV, `test_labels.csv`, `test_scores.csv` or training report. Default demo selection uses the highest detector score, without labels; it is intentionally a high-risk example and is not a representative evaluation of Qwen. As with other Python pickle formats, load only locally trusted model bundles.

Outputs under `artifacts/ulb/`:

- `model.joblib`: trained detector, feature schema, validation threshold and checksums.
- `training_report.json`: source, preprocessing, partitions, metrics, configuration and library versions.
- `test_features.csv`: held-out evidence without labels.
- `test_scores.csv`: detector scores and threshold flags, without labels.
- `test_labels.csv`: ground truth reserved for offline evaluation.

The fraud classifier's metrics measure detection. A successful Qwen investigation means it gathered evidence and submitted a permitted note. It does not establish that the note is factually flawless or that Qwen resists adversarial prompts. The tools do not execute real bank actions; cases are held in memory and the generated recommendation is saved in the report. These direct CLI commands run outside an OS sandbox. To use the separately verified runtime boundary, follow [the OpenShell guide](OPENSHELL.md).

The existing `investigate`, `evaluate` and FastAPI endpoints retain their fictional fixture behavior. Use `investigate-transaction` for real-data investigations.

## Limits of this benchmark

The dataset is old and covers only two days. It has no customer identifiers, so customer-disjoint splits cannot be verified. PCA was performed before publication; its original fit scope cannot be audited here. Anonymized components cannot justify stories about travel, devices or account takeover. Test metrics from this dataset are not estimates of modern banking performance, and the first Qwen demo is not a population-level agent evaluation.
