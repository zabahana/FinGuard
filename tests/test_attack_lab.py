import unittest
from finguard.attack_lab import application_cases, evaluate_calls
from finguard.ulb import TransactionBank, FEATURES


class AttackLabTests(unittest.TestCase):
    def bank(self):
        return TransactionBank({**{key:0.0 for key in FEATURES},'transaction_id':'ULB-TEST'},.9,.6)

    def test_actual_adapter_blocks_abuse_and_permits_controls(self):
        for name,calls,attack in application_cases('ULB-TEST'):
            with self.subTest(name=name):
                result=evaluate_calls(calls,self.bank())
                self.assertEqual(result['observed'],'denied' if attack else 'allowed')
                if name=='premature_submission':
                    self.assertEqual(result['application_events'],[])
                    self.assertTrue(result['adapter_replies'][0]['missing_evidence'])
                if name=='legitimate_submission':
                    self.assertEqual(result['workflow_status'],'complete')

    def test_runtime_not_claimed_when_adapter_rejects_call(self):
        result=evaluate_calls([{'function':{'name':'read_file','arguments':{'path':'/sealed/decoy.txt'}}}],self.bank())
        self.assertEqual(result['invalid_tool_calls'],1)
        self.assertEqual(result['application_events'],[])
