import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    import numpy as np
    import pandas as pd
    from finguard.fraud import FEATURES, chronological_split, metrics, prepare, select_threshold, sha256
    from finguard.ulb import TransactionBank, investigate_transaction, parse_call, load_bank
except ImportError:
    pd = None

from finguard.models import Action, Session, Task, Verdict
from finguard.runner import Runner


def call(name, **arguments):
    return {"function": {"name": name, "arguments": arguments}}


@unittest.skipIf(pd is None, "Optional fraud dependencies not installed")
class FraudTests(unittest.TestCase):
    def row(self):
        return {**{key: 0.0 for key in FEATURES}, "transaction_id": "ULB-000001"}

    def bank(self):
        return TransactionBank(self.row(), .8, .7)

    def test_deduplicate_and_split_without_time_overlap(self):
        rows = [{**{key: float(i) for key in FEATURES}, "Class": i % 2} for i in range(30)]
        rows.append(rows[0])
        frame = prepare(pd.DataFrame(rows))
        self.assertEqual(len(frame), 30)
        training, validation, test = chronological_split(frame)
        self.assertLess(training.Time.max(), validation.Time.min())
        self.assertLess(validation.Time.max(), test.Time.min())
        self.assertEqual(frame.transaction_id.nunique(), 30)
        self.assertEqual(training.iloc[0].transaction_id, "ULB-000001")

    def test_reject_conflicting_labels_and_missing_data(self):
        frame = pd.DataFrame([{**{key: 0.0 for key in FEATURES}, "Class": 0},
                              {**{key: 0.0 for key in FEATURES}, "Class": 1}])
        with self.assertRaises(ValueError):
            prepare(frame)
        frame.loc[0, "V1"] = np.nan
        with self.assertRaises(ValueError):
            prepare(frame)

    def test_threshold_and_confusion_counts(self):
        y = np.array([0, 0, 1, 1])
        scores = np.array([.1, .4, .3, .9])
        threshold, _ = select_threshold(y, scores)
        self.assertAlmostEqual(threshold, .9)
        result = metrics(y, scores, .35)
        self.assertEqual((result['true_positives'], result['false_positives'], result['false_negatives']), (1, 1, 1))

    def test_no_labels_or_other_transaction_reach_agent(self):
        bank = self.bank()
        session = Session(task=Task("ULB-000001", "ulb_transaction_review"))
        runner = Runner(session=session, bank=bank)
        for target in ("/api/transaction-evidence", "/api/risk-score"):
            decision, result = runner.act(Action("api", target, customer_id="ULB-000001"))
            self.assertEqual(decision.verdict, Verdict.ALLOW)
            self.assertNotIn('"Class"', json.dumps(result))
            decision, result = runner.act(Action("api", target, customer_id="ULB-000002"))
            self.assertEqual(decision.verdict, Verdict.DENY)
            self.assertIsNone(result)
        decision, _ = runner.act(Action("read", "/data/customers/C10452/profile.json"))
        self.assertEqual(decision.verdict, Verdict.DENY)
        with self.assertRaises(ValueError):
            TransactionBank({**self.row(), "Class": 1}, .8, .7)

    def test_label_lookup_and_argument_injection_rejected(self):
        for item in (call("get_label", transaction_id="ULB-000001"),
                     call("read_policy", path="test_labels.csv"),
                     call("risk_score", transaction_id="ULB-000001", Class=1)):
            with self.assertRaises(ValueError):
                parse_call(item)

    def test_feature_store_rejects_labels_and_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "test_features.csv"
            pd.DataFrame([{**self.row(), "Class": 1}]).to_csv(path, index=False)
            bundle = {"features": FEATURES, "test_features_sha256": sha256(path)}
            with patch("joblib.load", return_value=bundle):
                with self.assertRaisesRegex(ValueError, "unexpected fields or labels"):
                    load_bank(temporary)
                path.write_text("changed")
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    load_bank(temporary)

    def test_low_score_does_not_raise_alert(self):
        bank = TransactionBank(self.row(), .01, .7)
        result = bank.execute(Action("api", "/api/risk-score", customer_id="ULB-000001"))
        self.assertFalse(result["flagged_for_review"])

    def test_transaction_agent_completes_only_after_guarded_evidence(self):
        class Client:
            def __init__(self):
                self.index = 0
                self.messages = []
            def chat(self, messages):
                self.messages = messages
                calls = ([call("read_policy"), call("transaction_evidence", transaction_id="ULB-000001"),
                          call("risk_score", transaction_id="ULB-000001")] if self.index == 0 else
                         [call("submit_case", transaction_id="ULB-000001", text="Score 0.8 exceeds 0.7; review.")])
                self.index += 1
                return {"message": {"role": "assistant", "content": "", "tool_calls": calls}}
        client = Client()
        report, events = investigate_transaction(bank=self.bank(), client=client)
        self.assertEqual(report["status"], "complete")
        self.assertFalse(report["synthetic"])
        self.assertEqual(report["banking_actions"], "simulated")
        self.assertEqual(report["transaction_id"], "ULB-000001")
        self.assertNotIn("customer_id", report)
        self.assertEqual(len(events), 4)
        self.assertNotIn('"Class"', json.dumps(client.messages))
        self.assertNotIn("C10452", json.dumps(client.messages))
