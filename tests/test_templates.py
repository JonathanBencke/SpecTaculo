"""Testes de regressão dos templates (garantem que o body compartilhado
   continua sendo a fonte única dos 4 formatos)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from generate import TARGETS
from schema import AgentSpec

ROOT = Path(__file__).resolve().parent.parent
GENERATED = ROOT / "generated"
AGENTS_DIR = ROOT / "src" / "agents"


def _all_markdown_bodies() -> dict[str, str]:
    """Extrai o 'corpo' (tudo depois do frontmatter) de cada artefato MD."""
    out: dict[str, str] = {}
    for agent_path in sorted(AGENTS_DIR.glob("*.yml")):
        agent = AgentSpec.from_yaml(agent_path)
        for tool in ("claude", "kimi", "opencode"):
            rel = TARGETS[tool]["path"].format(name=agent.name)
            text = (GENERATED / rel).read_text(encoding="utf-8")
            # Tudo após o segundo '---' é o corpo.
            _, _, body = text.split("---", 2)
            out[f"{tool}:{agent.name}"] = body.lstrip()
    return out


def test_claude_kimi_opencode_bodies_are_identical() -> None:
    """Os 3 formatos markdown compartilham o mesmo corpo, EXCETO o
    orquestrador spectaculo-run — que recebe um bloco de dispatch
    específico por CLI (regressão intencional da Fase 3)."""
    bodies = _all_markdown_bodies()
    for agent_path in sorted(AGENTS_DIR.glob("*.yml")):
        name = AgentSpec.from_yaml(agent_path).name
        c = bodies[f"claude:{name}"]
        k = bodies[f"kimi:{name}"]
        o = bodies[f"opencode:{name}"]
        if name == "spectaculo-run":
            # não são idênticos, mas cada um menciona sua própria CLI
            for body, label in ((c, "Claude Code"), (k, "kimi-code"), (o, "opencode")):
                assert label in body, f"{name}/{label}"
        else:
            assert c == k == o, f"Bodies divergem para {name}"


@pytest.mark.parametrize(
    "section",
    ["## Entrada", "## Saída", "## Regras", "## Instruções", "## Handoff"],
)
def test_every_agent_body_has_required_section(section: str) -> None:
    bodies = _all_markdown_bodies()
    missing = [key for key, body in bodies.items() if section not in body]
    assert not missing, f"{section} ausente em: {missing}"


def test_handoff_block_present_in_all_agents_prompts() -> None:
    for path in sorted(AGENTS_DIR.glob("*.yml")):
        agent = AgentSpec.from_yaml(path)
        assert "## Handoff" in agent.prompt, path.name
        assert "Fase:" in agent.prompt, path.name
        assert "Status:" in agent.prompt, path.name


def test_body_template_uses_macro_not_duplicate_logic() -> None:
    """Os wrappers MD devem ser finos: apenas importam a macro body."""
    templates_dir = ROOT / "src" / "templates"
    for wrapper in ("claude-skill.md.j2", "kimi-skill.md.j2", "opencode-agent.md.j2"):
        content = (templates_dir / wrapper).read_text(encoding="utf-8")
        assert "from '_body.md.j2' import body" in content, wrapper
        assert "{{ body(" in content, wrapper


def test_kiro_systemprompt_matches_markdown_body() -> None:
    """O systemPrompt do kiro deve conter o mesmo conteúdo do corpo MD."""
    import json

    for path in sorted(AGENTS_DIR.glob("*.yml")):
        agent = AgentSpec.from_yaml(path)
        md_rel = TARGETS["claude"]["path"].format(name=agent.name)
        md_body = (GENERATED / md_rel).read_text(encoding="utf-8").split("---", 2)[2].strip()

        kiro_rel = TARGETS["kiro"]["path"].format(name=agent.name)
        data = json.loads((GENERATED / kiro_rel).read_text(encoding="utf-8"))
        # systemPrompt é o body + quebras; verificamos as linhas-chave.
        for key_line in ("# " + agent.name, "## Entrada", "## Instruções", "## Handoff"):
            assert key_line in data["systemPrompt"], f"{agent.name}: {key_line}"


# ---------------------------------------------------------------------------
# Fase 3: dispatch por CLI, STATE.json, limite de iterações
# ---------------------------------------------------------------------------

def test_orchestrator_has_per_cli_dispatch() -> None:
    """Cada CLI gera um bloco de dispatch distinto para o orquestrador."""
    cases = {
        "claude": "Claude Code",
        "kimi": "kimi-code",
        "opencode": "opencode",
    }
    for tool, label in cases.items():
        rel = TARGETS[tool]["path"].format(name="spectaculo-run")
        text = (GENERATED / rel).read_text(encoding="utf-8")
        assert "Dispatch específico da CLI" in text, tool
        assert label in text, f"{tool}: {label} ausente"
    # kiro guarda o systemPrompt em JSON
    kiro = json.loads(
        (GENERATED / TARGETS["kiro"]["path"].format(name="spectaculo-run")).read_text(
            encoding="utf-8"
        )
    )
    assert "kiro-cli" in kiro["systemPrompt"]
    assert "/agent swap" in kiro["systemPrompt"]


def test_non_orchestrator_agents_have_no_dispatch_block() -> None:
    for path in sorted(AGENTS_DIR.glob("*.yml")):
        agent = AgentSpec.from_yaml(path)
        if agent.name == "spectaculo-run":
            continue
        rel = TARGETS["opencode"]["path"].format(name=agent.name)
        text = (GENERATED / rel).read_text(encoding="utf-8")
        assert "Dispatch específico da CLI" not in text, agent.name


def test_state_json_template_exists_and_is_valid_shape() -> None:
    state = ROOT / "src" / "templates" / "state.json.j2"
    assert state.exists(), "state.json.j2 ausente"
    content = state.read_text(encoding="utf-8")
    for key in ("spec_id", "phase", "attempts", "max_attempts", "history"):
        assert key in content, f"state.json.j2 sem chave {key}"


def test_loop_agents_reference_attempts_and_max() -> None:
    """validate e review devem mencionar o contador de tentativas e o limite."""
    for name in ("spectaculo-validate", "spectaculo-review"):
        path = AGENTS_DIR / f"{name}.yml"
        prompt = AgentSpec.from_yaml(path).prompt
        assert "attempts" in prompt, name
        assert "max_attempts" in prompt, name


def test_intake_and_run_reference_state_json() -> None:
    for name in ("spectaculo-intake", "spectaculo-run"):
        prompt = AgentSpec.from_yaml(AGENTS_DIR / f"{name}.yml").prompt
        assert "STATE.json" in prompt, name


def test_task_md_template_exists() -> None:
    assert (ROOT / "src" / "templates" / "task.md.j2").exists()
