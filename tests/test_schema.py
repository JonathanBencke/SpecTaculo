"""Testes do modelo de validação AgentSpec."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from schema import AgentSpec

AGENTS_DIR = Path(__file__).resolve().parent.parent / "src" / "agents"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_payload() -> dict:
    return {
        "name": "spectaculo-example",
        "description": "Agente de exemplo para testes.",
        "entry": "Texto de entrada.",
        "output": "Arquivo de saída.",
        "rules": ["Regra 1.", "Regra 2."],
        "prompt": "Você é um agente de exemplo.",
    }


# ---------------------------------------------------------------------------
# Campos obrigatórios
# ---------------------------------------------------------------------------

def test_minimal_valid_spec(valid_payload: dict) -> None:
    agent = AgentSpec(**valid_payload)
    assert agent.name == "spectaculo-example"
    assert agent.mode == "subagent"  # default
    assert agent.tools is None  # default


@pytest.mark.parametrize("missing", ["name", "description", "entry", "output", "prompt"])
def test_required_fields_reject_empty(valid_payload: dict, missing: str) -> None:
    valid_payload[missing] = ""
    with pytest.raises(ValidationError):
        AgentSpec(**valid_payload)


@pytest.mark.parametrize("missing", ["name", "description", "entry", "output", "prompt"])
def test_required_fields_must_be_present(valid_payload: dict, missing: str) -> None:
    del valid_payload[missing]
    with pytest.raises(ValidationError):
        AgentSpec(**valid_payload)


# ---------------------------------------------------------------------------
# Nome em kebab-case
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "bad_name",
    [
        "Spectaculo-Run",   # maiúsculas
        "spectaculo_run",   # underscore
        "spectaculo run",   # espaço
        "-spectaculo-run",  # prefixo inválido
        "1spectaculo-run",  # inicia com número
        "spectaculo--run",  # duplo hífen
        "",                 # vazio
    ],
)
def test_invalid_name_rejected(bad_name: str, valid_payload: dict) -> None:
    valid_payload["name"] = bad_name
    with pytest.raises(ValidationError):
        AgentSpec(**valid_payload)


@pytest.mark.parametrize(
    "good_name",
    ["spectaculo-run", "spectaculo-intake", "a", "abc-123", "x-y-z"],
)
def test_valid_name_accepted(good_name: str, valid_payload: dict) -> None:
    valid_payload["name"] = good_name
    assert AgentSpec(**valid_payload).name == good_name


# ---------------------------------------------------------------------------
# Regras
# ---------------------------------------------------------------------------

def test_rules_strip_whitespace(valid_payload: dict) -> None:
    valid_payload["rules"] = ["  Regra com espaços.  ", "Outra regra."]
    agent = AgentSpec(**valid_payload)
    assert agent.rules == ["Regra com espaços.", "Outra regra."]


def test_rules_reject_blank_entries(valid_payload: dict) -> None:
    valid_payload["rules"] = ["Regra válida", "   "]
    with pytest.raises(ValidationError):
        AgentSpec(**valid_payload)


def test_rules_default_empty(valid_payload: dict) -> None:
    del valid_payload["rules"]
    assert AgentSpec(**valid_payload).rules == []


# ---------------------------------------------------------------------------
# mode / tools
# ---------------------------------------------------------------------------

def test_mode_invalid_rejected(valid_payload: dict) -> None:
    valid_payload["mode"] = "orchestrator"
    with pytest.raises(ValidationError):
        AgentSpec(**valid_payload)


def test_mode_primary_accepted(valid_payload: dict) -> None:
    valid_payload["mode"] = "primary"
    assert AgentSpec(**valid_payload).mode == "primary"


def test_tools_override(valid_payload: dict) -> None:
    valid_payload["tools"] = ["read", "write"]
    assert AgentSpec(**valid_payload).tools == ["read", "write"]


# ---------------------------------------------------------------------------
# extra = forbid
# ---------------------------------------------------------------------------

def test_unknown_field_rejected(valid_payload: dict) -> None:
    valid_payload["unknown_field"] = "surpresa"
    with pytest.raises(ValidationError):
        AgentSpec(**valid_payload)


# ---------------------------------------------------------------------------
# from_yaml
# ---------------------------------------------------------------------------

def test_all_committed_agents_load_successfully() -> None:
    """Garantia de que todo YAML em src/agents/ satisfaz o schema."""
    yml_files = sorted(AGENTS_DIR.glob("*.yml"))
    assert yml_files, "Esperado ao menos um agente em src/agents/."
    for path in yml_files:
        agent = AgentSpec.from_yaml(path)
        assert agent.name.startswith("spectaculo-"), path.name
        assert agent.prompt.strip(), path.name
        assert isinstance(agent.rules, list), path.name


def test_orchestrator_is_primary() -> None:
    run_yml = AGENTS_DIR / "spectaculo-run.yml"
    assert AgentSpec.from_yaml(run_yml).mode == "primary"


def test_other_agents_are_subagents() -> None:
    for path in sorted(AGENTS_DIR.glob("*.yml")):
        if path.stem == "spectaculo-run":
            continue
        assert AgentSpec.from_yaml(path).mode == "subagent", path.name
