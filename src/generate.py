#!/usr/bin/env python3
"""
Gera artefatos nativos de agentes/skills para múltiplas CLIs a partir de
uma fonte única em YAML.

Suporta:
- Claude Code (.claude/skills/<nome>/SKILL.md)
- kimi-code (.kimi-code/skills/<nome>/SKILL.md)
- opencode (.opencode/agents/<nome>.md)
- kiro-cli (.kiro/agents/<nome>.json)
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

# Permite execução tanto como script (python src/generate.py) quanto como
# pacote instalado (spectaculo-generate).
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from schema import AgentSpec  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC_AGENTS = ROOT / "src" / "agents"
TEMPLATES = ROOT / "src" / "templates"
GENERATED = ROOT / "generated"

TARGETS = {
    "claude": {
        "template": "claude-skill.md.j2",
        "path": ".claude/skills/{name}/SKILL.md",
    },
    "kimi": {
        "template": "kimi-skill.md.j2",
        "path": ".kimi-code/skills/{name}/SKILL.md",
    },
    "opencode": {
        "template": "opencode-agent.md.j2",
        "path": ".opencode/agents/{name}.md",
    },
    "kiro": {
        "template": "kiro-agent.json.j2",
        "path": ".kiro/agents/{name}.json",
    },
}


def load_agent(path: Path) -> AgentSpec:
    """Carrega e valida um agente a partir de um YAML."""
    return AgentSpec.from_yaml(path)


def _tojson_unicode(value, indent: int = 2) -> str:
    return json.dumps(value, ensure_ascii=False, indent=indent)


def render(tool: str, agent: AgentSpec) -> str:
    config = TARGETS[tool]
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["tojson_unicode"] = _tojson_unicode
    template = env.get_template(config["template"])
    context = agent.model_dump()
    context["tool"] = tool
    rendered = template.render(**context)
    return rendered.lstrip("\n")


def _clean_target_root(tool: str) -> Path:
    """Diretório-base a ser removido no --clean.

    Calcula o ancestral comum do padrão de saída (antes do placeholder
    {name}). Funciona para paths com {name} em diretório (Claude/kimi/opencode)
    ou como nome de arquivo (kiro).
    """
    pattern = TARGETS[tool]["path"]
    pre = pattern.split("{name}", 1)[0].rstrip("/\\")
    return GENERATED / pre


def generate(tool: str, clean: bool = False) -> None:
    if tool not in TARGETS and tool != "all":
        print(f"Ferramenta desconhecida: {tool}", file=sys.stderr)
        sys.exit(1)

    tools = list(TARGETS.keys()) if tool == "all" else [tool]

    for t in tools:
        target_dir = _clean_target_root(t)
        if clean and target_dir.exists():
            shutil.rmtree(target_dir)

    errors: list[tuple[Path, Exception]] = []
    for agent_file in sorted(SRC_AGENTS.glob("*.yml")):
        try:
            agent = load_agent(agent_file)
        except Exception as exc:
            errors.append((agent_file, exc))
            print(f"[!] YAML inválido: {agent_file.name} -> {exc}", file=sys.stderr)
            continue

        name = agent.name
        for t in tools:
            relative_path = TARGETS[t]["path"].format(name=name)
            output_path = GENERATED / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            rendered = render(t, agent)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered)
            print(f"Gerado: {output_path.relative_to(ROOT)}")

    if errors:
        print(
            f"\n[x] {len(errors)} agente(s) com YAML inválido. Build abortado.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera skills/agentes SDD para CLIs suportadas."
    )
    parser.add_argument(
        "tool",
        choices=["claude", "kimi", "opencode", "kiro", "all"],
        help="Ferramenta alvo (ou 'all' para todas).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Limpa os artefatos gerados antes de gerar novamente.",
    )
    args = parser.parse_args()
    generate(args.tool, clean=args.clean)


if __name__ == "__main__":
    main()
