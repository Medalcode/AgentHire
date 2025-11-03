import pytest
from connectors.base import BaseConnector

class DummyConnector(BaseConnector):
    async def search_jobs(self, keywords, location="", modality="", max_results=50):
        return []
    
    def _normalize(self, raw):
        return raw

def test_detect_modality():
    connector = DummyConnector()
    assert connector._detect_modality("trabajo remoto") == "remote"
    assert connector._detect_modality("trabajo híbrido") == "hybrid"
    assert connector._detect_modality("trabajo presencial") == "presencial"
    assert connector._detect_modality("no dice nada") == "unknown"
