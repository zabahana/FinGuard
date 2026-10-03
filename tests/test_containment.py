import errno
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

from finguard.contained import FileTransactionBank
from finguard.containment_probes import network_probe
from finguard.llm import OllamaClient
from finguard.ulb import FEATURES


class ContainmentTests(unittest.TestCase):
    def test_remote_model_endpoint_is_rejected(self):
        with self.assertRaises(ValueError):
            OllamaClient(endpoint='https://example.com/api/chat')
        client = OllamaClient(endpoint='http://host.openshell.internal:11434/api/chat')
        self.assertEqual(client.endpoint, 'http://host.openshell.internal:11434/api/chat')

    def test_permission_denial_is_not_confused_with_network_failure(self):
        cases = [(PermissionError(errno.EACCES, 'denied'), 'denied'),
                 (TimeoutError('timeout'), 'inconclusive'),
                 (ConnectionRefusedError(errno.ECONNREFUSED, 'refused'), 'inconclusive')]
        for reason, expected in cases:
            with patch('finguard.containment_probes.build_opener') as opener:
                opener.return_value.open.side_effect = URLError(reason)
                report = network_probe('probe', 18082, '/collect', 'POST', 'denied')
                self.assertEqual(report['observed'], expected)
                self.assertEqual(report['passed'], expected == 'denied')

    def test_exported_evidence_rejects_label_injection(self):
        with tempfile.TemporaryDirectory() as temporary:
            row = {**{k: 0.0 for k in FEATURES}, 'transaction_id': 'ULB-000001', 'Class': 1}
            Path(temporary, 'transaction.json').write_text(json.dumps({'row': row, 'score': .5, 'threshold': .7}))
            with self.assertRaises(ValueError):
                FileTransactionBank(temporary)
