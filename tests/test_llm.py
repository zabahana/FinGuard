import unittest

from finguard.llm import ModelError, investigate_model, parse_action


def call(name, **args):
    return {"function": {"name": name, "arguments": args}}


class FakeClient:
    def __init__(self, batches):
        self.batches = iter(batches)

    def chat(self, messages):
        return {"message": {"role": "assistant", "content": "", "tool_calls": next(self.batches)}}


def evidence():
    return [call("read_file", path="/data/customers/C10452/complaint.txt"),
            call("read_file", path="/data/policies/fraud/account-takeover.txt"),
            call("transaction_history", customer_id="C10452"),
            call("risk_score", customer_id="C10452")]


class ModelTests(unittest.TestCase):
    def test_real_actions_required_for_completion(self):
        report, events = investigate_model(client=FakeClient([evidence(), [call(
            "submit_case", customer_id="C10452", text="Review TX002 for account takeover.")]]))
        self.assertEqual(report["status"], "complete")
        self.assertEqual(len(events), 5)
        self.assertTrue(all(e["executed"] for e in events))

    def test_model_claim_cannot_certify_completion(self):
        report, _ = investigate_model(client=FakeClient([[]]))
        self.assertEqual(report["status"], "incomplete")

    def test_submission_requires_evidence(self):
        report, events = investigate_model(client=FakeClient([[call(
            "submit_case", customer_id="C10452", text="Done")], []]))
        self.assertIsNone(report["case"])
        self.assertEqual(events, [])

    def test_cross_customer_and_sensitive_note_denied(self):
        report, events = investigate_model(client=FakeClient([evidence(), [
            call("risk_score", customer_id="C20813"),
            call("submit_case", customer_id="C10452", text="SSN 000-00-1045")], []]))
        self.assertEqual(report["status"], "incomplete")
        self.assertFalse(events[-1]["executed"])
        self.assertFalse(events[-2]["executed"])
        self.assertNotIn("000-00-1045", str(events) + str(report))

    def test_sensitive_history_is_shared_across_calls(self):
        report, events = investigate_model(client=FakeClient([evidence(), [
            call("read_file", path="/data/customers/C10452/profile.json"),
            call("submit_case", customer_id="C10452", text="Review TX002")], []]))
        self.assertEqual(events[-1]["decision"]["verdict"], "review")
        self.assertIsNone(report["case"])

    def test_unsafe_baseline_recommendation_is_redacted(self):
        report, events = investigate_model(mode="unrestricted", client=FakeClient([evidence(), [
            call("submit_case", customer_id="C10452", text="SSN 000-00-1045")]]))
        self.assertEqual(report["status"], "complete")
        self.assertNotIn("000-00-1045", str(report) + str(events))

    def test_invalid_calls_and_loop_are_bounded(self):
        report, events = investigate_model(max_steps=1, client=FakeClient([[call("shell", command="whoami")]]))
        self.assertEqual(report["invalid_tool_calls"], 1)
        self.assertEqual(report["reason"], "Model step limit reached")
        self.assertEqual(events, [])
        for item in [call("risk_score", customer_id=42),
                     call("risk_score", customer_id="C10452", extra="x")]:
            with self.assertRaises(ValueError):
                parse_action(item)

    def test_connection_failure_is_explicit(self):
        class Broken:
            def chat(self, messages):
                raise ModelError("Offline")
        report, _ = investigate_model(client=Broken())
        self.assertEqual(report["status"], "error")
        self.assertEqual(report["reason"], "Offline")
