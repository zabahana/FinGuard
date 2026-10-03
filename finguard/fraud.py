"""Reproducible ULB fraud training; labels never enter the agent feature store."""
import hashlib
import json
import platform
from pathlib import Path
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (average_precision_score, confusion_matrix,
                             precision_recall_curve, roc_auc_score)
from threadpoolctl import threadpool_limits

SOURCE = "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud"
CSV_SHA256 = "76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89"
FEATURES = ["Time", *[f"V{i}" for i in range(1, 29)], "Amount"]
DEFAULT_CSV = ".local/datasets/ulb/creditcard.csv"
DEFAULT_OUTPUT = "artifacts/ulb"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare(frame):
    if set(frame.columns) != set(FEATURES + ["Class"]):
        raise ValueError("Expected the original ULB schema: Time, V1..V28, Amount, Class")
    frame = frame[FEATURES + ["Class"]].apply(pd.to_numeric, errors="raise")
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError("Dataset contains missing or non-finite values")
    if not frame["Class"].isin([0, 1]).all():
        raise ValueError("Class must contain only 0 and 1")
    if (frame[["Time", "Amount"]] < 0).any().any():
        raise ValueError("Time and Amount must be nonnegative")
    duplicates = frame[frame.duplicated(FEATURES, keep=False)]
    if not duplicates.empty and duplicates.groupby(FEATURES)["Class"].nunique().max() > 1:
        raise ValueError("Identical feature rows have conflicting labels")
    frame = frame.copy()
    # Stable source row identifiers, never presented as customer/account identifiers.
    frame["transaction_id"] = [f"ULB-{i:06d}" for i in range(1, len(frame) + 1)]
    return frame.drop_duplicates(FEATURES).sort_values("Time", kind="stable").reset_index(drop=True)


def chronological_split(frame):
    times = frame["Time"].to_numpy()
    if len(frame) < 10 or not frame["Time"].is_monotonic_increasing:
        raise ValueError("Need at least ten chronologically sorted rows")
    # Keep equal timestamps together, so no future timestamp reaches an earlier partition.
    a = int(np.searchsorted(times, times[int(len(times) * .6)], side="left"))
    b = int(np.searchsorted(times, times[int(len(times) * .8)], side="left"))
    parts = (frame.iloc[:a], frame.iloc[a:b], frame.iloc[b:])
    if any(part.empty or part["Class"].nunique() != 2 for part in parts):
        raise ValueError("Each chronological partition must contain both labels")
    return parts


def select_threshold(labels, scores, target_precision=.90):
    precision, recall, thresholds = precision_recall_curve(labels, scores)
    eligible = np.flatnonzero(precision[:-1] >= target_precision)
    if len(eligible):
        best = eligible[np.argmax(recall[eligible])]
        strategy = "maximum validation recall at precision >= 0.90"
    else:
        f1 = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-15)
        best = int(np.argmax(f1))
        strategy = "fallback: maximum validation F1; precision target unattainable"
    return float(thresholds[best]), strategy


def metrics(labels, scores, threshold):
    tn, fp, fn, tp = confusion_matrix(labels, scores >= threshold, labels=[0, 1]).ravel()
    return {"rows": len(labels), "fraud_count": int(np.sum(labels)),
            "fraud_prevalence": float(np.mean(labels)),
            "average_precision": float(average_precision_score(labels, scores)),
            "roc_auc": float(roc_auc_score(labels, scores)),
            "precision": float(tp / (tp + fp)) if tp + fp else 0.0,
            "recall": float(tp / (tp + fn)) if tp + fn else 0.0,
            "true_positives": int(tp), "false_positives": int(fp),
            "false_negatives": int(fn), "true_negatives": int(tn)}


def train(csv_path=DEFAULT_CSV, output=DEFAULT_OUTPUT):
    csv_path, destination = Path(csv_path), Path(output)
    digest = sha256(csv_path)
    if digest != CSV_SHA256:
        raise ValueError("CSV checksum differs from the verified ULB source; refusing silent dataset substitution")
    raw = pd.read_csv(csv_path)
    frame = prepare(raw)
    training, validation, test = chronological_split(frame)
    model = HistGradientBoostingClassifier(max_iter=150, max_leaf_nodes=15,
        learning_rate=.08, l2_regularization=1.0, class_weight="balanced",
        early_stopping=False, random_state=42)
    with threadpool_limits(limits=4):
        model.fit(training[FEATURES], training["Class"])
        validation_scores = model.predict_proba(validation[FEATURES])[:, 1]
        threshold, strategy = select_threshold(validation["Class"], validation_scores)
        test_scores = model.predict_proba(test[FEATURES])[:, 1]
    destination.mkdir(parents=True, exist_ok=True)
    feature_path = destination / "test_features.csv"
    test[["transaction_id"] + FEATURES].to_csv(feature_path, index=False)
    # Evaluation-only file. The banking backend never opens this file or the raw CSV.
    test[["transaction_id", "Class"]].to_csv(destination / "test_labels.csv", index=False)
    pd.DataFrame({"transaction_id": test["transaction_id"], "score": test_scores,
                  "flagged": test_scores >= threshold}).to_csv(destination / "test_scores.csv", index=False)
    bundle = {"model": model, "features": FEATURES, "threshold": threshold,
              "source_sha256": digest, "test_features_sha256": sha256(feature_path),
              "sklearn_version": sklearn.__version__}
    joblib.dump(bundle, destination / "model.joblib")
    report = {"source": SOURCE, "source_sha256": digest,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "raw_rows": len(raw), "raw_fraud_count": int(raw["Class"].sum()),
        "duplicates_removed": len(raw) - len(frame), "retained_rows": len(frame),
        "retained_fraud_count": int(frame["Class"].sum()),
        "split": "chronological 60/20/20 by rows, equal timestamps kept together",
        "partitions": {name: {"rows": len(part), "fraud_count": int(part["Class"].sum()),
                               "time_min_seconds": float(part["Time"].min()),
                               "time_max_seconds": float(part["Time"].max())}
                       for name, part in zip(("train", "validation", "test"), (training, validation, test))},
        "estimator": type(model).__name__, "parameters": model.get_params(),
        "score_interpretation": "Uncalibrated ranking score; not a fraud probability",
        "threshold": threshold, "threshold_selection": strategy,
        "validation": metrics(validation["Class"], validation_scores, threshold),
        "test": metrics(test["Class"], test_scores, threshold),
        "demo_transaction_id": str(test.iloc[int(np.argmax(test_scores))]["transaction_id"]),
        "demo_selection": "highest model score in test partition, without consulting test labels",
        "environment": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                        "pandas": pd.__version__, "numpy": np.__version__},
        "limitations": ["Two days of 2013 data; not evidence of present-day production performance",
                        "PCA features have no public semantic meanings; currency and customer identities unavailable",
                        "No customer IDs: customer-level train/test separation cannot be verified",
                        "Published PCA transformation was performed upstream; its fit scope is unavailable",
                        "Threshold selected only on validation; no hyperparameter search or test-based tuning",
                        "Qwen investigation quality is separate from these detector metrics"]}
    (destination / "training_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
