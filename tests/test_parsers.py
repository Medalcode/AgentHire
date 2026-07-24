import pytest
from agents.core.llm_client import _parse_json_from_llm

def test_parse_json_valid_object():
    """Prueba que un objeto JSON válido se parsea correctamente."""
    raw = '{"status": "ok", "score": 85}'
    result = _parse_json_from_llm(raw)
    assert result == {"status": "ok", "score": 85}

def test_parse_json_valid_array():
    """Prueba que un array JSON válido se parsea correctamente."""
    raw = '[{"title": "Dev"}, {"title": "QA"}]'
    result = _parse_json_from_llm(raw)
    assert result == [{"title": "Dev"}, {"title": "QA"}]

def test_parse_json_markdown_fences():
    """Prueba que remueve los code fences de Markdown."""
    raw = '''```json
{"key": "value"}
```'''
    result = _parse_json_from_llm(raw)
    assert result == {"key": "value"}

def test_parse_json_fallback_object():
    """Prueba que extrae un objeto JSON si hay texto basura alrededor."""
    raw = 'Aquí está el resultado:\n\n{"key": "value"}\n\nEspero sirva.'
    result = _parse_json_from_llm(raw)
    assert result == {"key": "value"}

def test_parse_json_fallback_array():
    """Prueba que extrae un array JSON si hay texto basura alrededor."""
    raw = 'Trabajos encontrados:\n\n[{"id": 1}]\n\nFin.'
    result = _parse_json_from_llm(raw)
    assert result == [{"id": 1}]

def test_parse_json_invalid():
    """Prueba que levanta un ValueError si no hay JSON válido."""
    raw = 'No encontré ningún trabajo.'
    with pytest.raises(ValueError):
        _parse_json_from_llm(raw)
