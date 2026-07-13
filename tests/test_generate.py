"""Testes do gerador de artefatos (src/generate.py)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import generate as generate_mod
from generate import TARGETS, _clean_target_root, generate, render

ROOT = Path(__file__).resolve().parent.parent
GENERATED = ROOT / "generated"

EXPECTED_AGENTS = [
    "spectaculo-run",
    "spectaculo-intake",
    "spectaculo-spec",
    "spectaculo-validate",
    "spectaculo-plan",
    "spectaculo-execute",
    "spectaculo-review",
]

ALL_TOOLS = ["claude", "kimi", "opencode", "kiro"]


# ---------------------------------------------------------------------------
# _clean_target_root — bug histórico do kiro
# ---------------------------------------------------------------------------

def test_clean_target_root_returns_existing_dir_for_each_tool() -> None:
    """Para TODAS as CLIs, o dir-base de clean deve ser o ancestral correto
    (sem sobras de placeholder {name}). Regressão do bug do kiro."""
    for tool in ALL_TOOLS:
        root = _clean_target_root(tool)
        assert "{name}" not in str(root), tool
        assert root.is_relative_to(GENERATED), tool


def test_clean_target_root_kiro_specifically() -> None:
    """O bug original: kiro usava .split('/{name}/') que não casava e
    deixava '{name}.json' no caminho. Agora deve apontar para .kiro/agents."""
    root = _clean_target_root("kiro")
    assert root == (GENERATED / ".kiro" / "agents").resolve() or root.name == "agents"


# ---------------------------------------------------------------------------
# Geração end-to-end
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def _regenerate_all(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Gera todos os artefatos uma vez antes dos testes deste módulo."""
    generate("all", clean=True)


def test_generates_expected_path_per_tool_and_agent() -> None:
    for agent in EXPECTED_AGENTS:
        for tool in ALL_TOOLS:
            relative = TARGETS[tool]["path"].format(name=agent)
            assert (GENERATED / relative).exists(), f"{tool}:{agent}"


def test_all_artifacts_are_non_empty() -> None:
    for agent in EXPECTED_AGENTS:
        for tool in ALL_TOOLS:
            relative = TARGETS[tool]["path"].format(name=agent)
            content = (GENERATED / relative).read_text(encoding="utf-8")
            assert content.strip(), f"{tool}:{agent} vazio"


def test_total_artifact_count() -> None:
    files = [p for p in GENERATED.rglob("*") if p.is_file()]
    assert len(files) == len(EXPECTED_AGENTS) * len(ALL_TOOLS)


# ---------------------------------------------------------------------------
# Conteúdo por formato
# ---------------------------------------------------------------------------

def test_markdown_artifacts_have_frontmatter_and_body() -> None:
    for tool in ("claude", "kimi", "opencode"):
        path = GENERATED / TARGETS[tool]["path"].format(name="spectaculo-run")
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"{tool} sem frontmatter"
        assert "name: spectaculo-run" in text
        assert "# spectaculo-run" in text
        assert "## Instruções" in text


def test_opencode_run_agent_is_marked_primary() -> None:
    path = GENERATED / TARGETS["opencode"]["path"].format(name="spectaculo-run")
    text = path.read_text(encoding="utf-8")
    assert "mode: primary" in text


def test_opencode_subagent_is_marked_subagent() -> None:
    path = GENERATED / TARGETS["opencode"]["path"].format(name="spectaculo-intake")
    text = path.read_text(encoding="utf-8")
    assert "mode: subagent" in text


def test_kiro_artifacts_are_valid_json() -> None:
    for agent in EXPECTED_AGENTS:
        path = GENERATED / TARGETS["kiro"]["path"].format(name=agent)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["name"] == agent
        assert data["systemPrompt"].lstrip().startswith("# " + agent)
        assert data["mode"] in ("primary", "subagent")


def test_kiro_json_has_escaped_systemprompt() -> None:
    path = GENERATED / TARGETS["kiro"]["path"].format(name="spectaculo-spec")
    raw = path.read_text(encoding="utf-8")
    # O systemPrompt deve estar numa única linha JSON (sem quebras de linha reais).
    data = json.loads(raw)
    assert "\n" not in data["systemPrompt"][:-1] or data["systemPrompt"].endswith("\n")
    # round-trip válido
    json.dumps(data, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Idempotência e clean
# ---------------------------------------------------------------------------

def test_generate_is_idempotent(tmp_path: Path) -> None:
    """Rodar generate duas vezes produz o mesmo conteúdo (não acrescenta lixo)."""
    rel = TARGETS["claude"]["path"].format(name="spectaculo-intake")
    before = (GENERATED / rel).read_text(encoding="utf-8")
    generate("claude")
    after = (GENERATED / rel).read_text(encoding="utf-8")
    assert before == after


def test_clean_removes_old_artifacts() -> None:
    # Cria um arquivo órfão propositalmente na árvore do claude.
    orphan_dir = GENERATED / ".claude" / "skills" / "spectaculo-ghost"
    orphan_dir.mkdir(parents=True, exist_ok=True)
    orphan = orphan_dir / "SKILL.md"
    orphan.write_text("ghost", encoding="utf-8")
    assert orphan.exists()

    generate("claude", clean=True)
    assert not orphan.exists(), "clean não removeu agente fantasma"
    # agentes reais continuam presentes
    assert (
        GENERATED / TARGETS["claude"]["path"].format(name="spectaculo-run")
    ).exists()


def test_clean_works_for_kiro_too() -> None:
    """Regressão direta do bug original: clean do kiro não limpava nada."""
    orphan = GENERATED / ".kiro" / "agents" / "ghost.json"
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_text("{}", encoding="utf-8")

    generate("kiro", clean=True)
    assert not orphan.exists()
    assert (
        GENERATED / TARGETS["kiro"]["path"].format(name="spectaculo-run")
    ).exists()


# ---------------------------------------------------------------------------
# Tratamento de erro — YAML inválido aborta o build
# ---------------------------------------------------------------------------

def test_invalid_yaml_aborts_build_with_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    fake_agents = tmp_path / "agents"
    fake_agents.mkdir()
    (fake_agents / "bad.yml").write_text(
        "name: Bad_Name\n"  # maiúscula -> inválido
        "description: x\nentry: x\noutput: x\nrules: []\nprompt: x\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(generate_mod, "SRC_AGENTS", fake_agents)
    monkeypatch.setattr(generate_mod, "GENERATED", tmp_path / "generated")

    with pytest.raises(SystemExit) as exc:
        generate("claude", clean=True)
    assert exc.value.code != 0
    err = capsys.readouterr().err
    assert "YAML inválido" in err
