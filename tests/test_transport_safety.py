from __future__ import annotations

import unittest
from unittest import mock

import semantic_entropy


class _FakeResponse:
    def __init__(self, payload, headers=None):
        self.payload = payload
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, size):
        return self.payload[:size]


class _FakeOpener:
    def __init__(self, response):
        self.response = response

    def open(self, target, timeout):
        return self.response


class TransportSafetyTests(unittest.TestCase):
    def request_with(self, response, *, max_response_bytes=64):
        opener = _FakeOpener(response)
        with mock.patch.object(semantic_entropy.urllib.request, "build_opener", return_value=opener):
            return semantic_entropy._json_request(
                "http://127.0.0.1:1234/v1/models",
                timeout=2,
                max_response_bytes=max_response_bytes,
            )

    def test_endpoint_normalization_and_path_join(self) -> None:
        self.assertEqual(
            semantic_entropy._normalize_endpoint("http://127.0.0.1:1234/v1/"),
            "http://127.0.0.1:1234/v1",
        )

    def test_endpoint_rejects_credential_query_and_fragment_channels(self) -> None:
        bad = (
            "http://user:secret@127.0.0.1/v1",
            "http://127.0.0.1/v1?token=secret",
            "http://127.0.0.1/v1#fragment",
            "file:///tmp/models.json",
        )
        for endpoint in bad:
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(ValueError):
                    semantic_entropy._normalize_endpoint(endpoint)

    def test_redirect_handler_refuses_redirects(self) -> None:
        handler = semantic_entropy._NoRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, "Found", {}, "http://other"))

    def test_declared_oversize_response_is_rejected_before_read(self) -> None:
        with self.assertRaisesRegex(ValueError, "exceeds byte ceiling"):
            self.request_with(
                _FakeResponse(b"", {"Content-Length": "1024"}),
            )

    def test_streamed_oversize_response_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "exceeds byte ceiling"):
            self.request_with(
                _FakeResponse(b'{"data":"' + (b"x" * 256) + b'"}'),
            )

    def test_small_json_response_is_accepted(self) -> None:
        self.assertEqual(
            self.request_with(_FakeResponse(b'{"ok":true}')),
            {"ok": True},
        )


if __name__ == "__main__":
    unittest.main()
