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

def test_parse_salary_range():
    connector = DummyConnector()
    assert connector._parse_salary("1.500.000 - 2.000.000") == (1500000, 2000000)

def test_parse_salary_single():
    connector = DummyConnector()
    assert connector._parse_salary("800000") == (800000, 800000)

def test_parse_salary_empty():
    connector = DummyConnector()
    assert connector._parse_salary("") == (None, None)
