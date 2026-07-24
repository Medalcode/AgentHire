import pytest
from fastapi.testclient import TestClient
import os

# Importamos las apps de los agentes
from agents.discovery.main import app as discovery_app
from agents.apply.main import app as apply_app
from agents.tracker.main import app as tracker_app

@pytest.fixture
def discovery_client():
    return TestClient(discovery_app)

@pytest.fixture
def apply_client():
    return TestClient(apply_app)

@pytest.fixture
def tracker_client():
    return TestClient(tracker_app)

def test_discovery_health(discovery_client):
    """Prueba que el Discovery Agent responde al health check."""
    response = discovery_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "agent": "discovery"}

def test_apply_health(apply_client):
    """Prueba que el Apply Agent responde al health check."""
    response = apply_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "agent": "apply"}

def test_tracker_health(tracker_client):
    """Prueba que el Tracker Agent responde al health check."""
    response = tracker_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "agent": "tracker"}
