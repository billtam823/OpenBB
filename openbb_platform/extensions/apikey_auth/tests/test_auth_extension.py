"""Tests for the API key auth extension."""

import json

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from openbb_apikey_auth.auth_extension import auth_hook


@pytest.fixture
def client():
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(auth_hook)])
    def _protected():
        return {"ok": True}

    return TestClient(app)


def test_valid_key_allows(client, monkeypatch):
    monkeypatch.setenv("OPENBB_API_KEYS", json.dumps({"thesisguard": "secret-123"}))  # pragma: allowlist secret
    resp = client.get("/protected", headers={"x-api-key": "secret-123"})  # pragma: allowlist secret
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_unknown_key_rejected(client, monkeypatch):
    monkeypatch.setenv("OPENBB_API_KEYS", json.dumps({"thesisguard": "secret-123"}))  # pragma: allowlist secret
    resp = client.get("/protected", headers={"x-api-key": "wrong"})
    assert resp.status_code == 401


def test_missing_header_rejected(client, monkeypatch):
    monkeypatch.setenv("OPENBB_API_KEYS", json.dumps({"thesisguard": "secret-123"}))  # pragma: allowlist secret
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_empty_config_fails_closed(client, monkeypatch):
    monkeypatch.delenv("OPENBB_API_KEYS", raising=False)
    monkeypatch.delenv("OPENBB_API_KEYS_FILE", raising=False)
    resp = client.get("/protected", headers={"x-api-key": "anything"})
    assert resp.status_code == 401


def test_invalid_json_fails_closed(client, monkeypatch):
    monkeypatch.setenv("OPENBB_API_KEYS", "not json{")
    resp = client.get("/protected", headers={"x-api-key": "anything"})
    assert resp.status_code == 401


def test_second_client_key_also_valid(client, monkeypatch):
    monkeypatch.setenv("OPENBB_API_KEYS", json.dumps({"a": "key-a", "b": "key-b"}))  # pragma: allowlist secret
    assert client.get("/protected", headers={"x-api-key": "key-a"}).status_code == 200  # pragma: allowlist secret
    assert client.get("/protected", headers={"x-api-key": "key-b"}).status_code == 200  # pragma: allowlist secret
