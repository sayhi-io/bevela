"""Regression for the chunked-response cleanup race observed in frozen study v1."""
import http.client
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from experiments.qwen_code_adapter import Relay


class ChunkedShutdownTests(unittest.TestCase):
    def test_unexpected_client_cleanup_error_also_fences_completion(self):
        with tempfile.TemporaryDirectory(prefix='qwen-relay-cleanup-error-') as temporary:
            path = Path(temporary) / 'transport.jsonl'
            relay = Relay('http://127.0.0.1:1/v1', path)
            shutdown = relay.server.shutdown_request

            def broken_shutdown(request):
                shutdown(request)
                raise AttributeError('PRIVATE_RAW_CONTENT')

            with patch.object(relay.server, 'shutdown_request', side_effect=broken_shutdown):
                with self.assertRaisesRegex(RuntimeError, 'refusing to finalize'):
                    with relay as endpoint:
                        try:
                            urlopen(Request(endpoint + '/unsupported', data=b'{}'), timeout=5)
                        except HTTPError as error:
                            self.assertEqual(error.code, 404)
                            error.close()
            self.assertEqual(relay.handler_errors, ['AttributeError'])
            self.assertNotIn('PRIVATE_RAW_CONTENT', path.read_text())
            self.assertFalse(relay.handlers)

    def test_unexpected_response_observer_error_fences_completion(self):
        response = b'data: {"choices":[null]}\n\n'

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(response)

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory(prefix='qwen-relay-error-') as temporary:
                path = Path(temporary) / 'transport.jsonl'
                relay = Relay(f'http://127.0.0.1:{server.server_port}/v1', path)
                with self.assertRaisesRegex(RuntimeError, 'refusing to finalize'):
                    with relay as endpoint:
                        with urlopen(Request(endpoint + '/chat/completions',
                                             data=b'{"stream":true}'), timeout=5) as reply:
                            self.assertEqual(reply.read(), response)
                self.assertEqual(relay.handler_errors, ['AttributeError'])
                events = [json.loads(line) for line in path.read_text().splitlines()]
                errors = [e for e in events if e['event'] == 'handler_error']
                self.assertEqual(len(errors), 1)
                self.assertEqual(errors[0]['type'], 'AttributeError')
                self.assertNotIn('message', errors[0])
                self.assertFalse(relay.handlers)
                self.assertFalse(relay.connections)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_logging_failure_still_fences_handler_completion(self):
        with tempfile.TemporaryDirectory(prefix='qwen-relay-log-error-') as temporary:
            path = Path(temporary) / 'transport.jsonl'
            relay = Relay('http://127.0.0.1:1/v1', path)
            with patch.object(relay, 'log', side_effect=OSError('PRIVATE_RAW_CONTENT')):
                with self.assertRaisesRegex(RuntimeError, 'refusing to finalize'):
                    with relay as endpoint:
                        with self.assertRaises(http.client.RemoteDisconnected):
                            urlopen(Request(endpoint + '/chat/completions', data=b'{}'), timeout=5)
            self.assertEqual(relay.handler_errors, ['OSError'])
            self.assertNotIn('PRIVATE_RAW_CONTENT', path.read_text())
            self.assertFalse(relay.handlers)

    def test_only_handler_closes_its_upstream_connection(self):
        release = threading.Event()
        sent = threading.Event()
        errors, closes = [], []

        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            def log_message(self, *_):
                pass
            def do_POST(self):
                self.rfile.read(int(self.headers['Content-Length']))
                self.send_response(200)
                self.send_header('Transfer-Encoding', 'chunked')
                self.end_headers()
                self.wfile.write(b'a\r\ndata: {}\n\n\r\n')
                self.wfile.flush()
                sent.set()
                release.wait(10)
                self.close_connection = True

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        original_close = http.client.HTTPConnection.close
        owner = threading.current_thread()

        def close(connection):
            if connection.port == server.server_port:
                closes.append(threading.current_thread())
            return original_close(connection)

        try:
            with tempfile.TemporaryDirectory(prefix='qwen-chunked-regression-') as temporary:
                relay = Relay(f'http://127.0.0.1:{server.server_port}/v1', Path(temporary) / 'transport.jsonl')
                relay.server.handle_error = lambda *_: errors.append(sys.exc_info()[1])
                with patch.object(http.client.HTTPConnection, 'close', close):
                    with relay as endpoint:
                        reply = urlopen(Request(endpoint + '/chat/completions', data=b'{"stream":true}'), timeout=5)
                        self.assertTrue(sent.wait(2))
                        self.assertEqual(reply.read(10), b'data: {}\n\n')
                    reply.close()
                self.assertTrue(closes)
                self.assertNotIn(owner, closes, 'Main-thread close races HTTPResponse reader cleanup')
                self.assertFalse(errors)
                self.assertFalse(relay.handlers)
                self.assertFalse(relay.connections)
        finally:
            release.set()
            server.shutdown()
            server.server_close()


if __name__ == '__main__':
    unittest.main()
