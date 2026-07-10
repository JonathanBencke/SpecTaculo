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
import os
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

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


def load_agent(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _tojson_unicode(value, indent: int = 2) -> str:
    return json.dumps(value, ensure_ascii=False, indent=indent)


def render(tool: str, agent: dict) -> str:
    config = TARGETS[tool]
    env = Environment(loader=FileSystemLoader(TEMPLATES))
    env.filters["tojson_unicode"] = _tojson_unicode
    template = env.get_template(config["template"])
    return template.render(**agent)


def generate(tool: str, clean: bool = False) -> None:
    if tool not in TARGETS and tool != "all":
        print(f"Ferramenta desconhecida: {tool}", file=sys.stderr)
        sys.exit(1)

    tools = list(TARGETS.keys()) if tool == "all" else [tool]

    for t in tools:
        target_dir = GENERATED / TARGETS[t]["path"].split("/{name}/")[0]
        if clean and target_dir.exists():
            import shutil
            shutil.rmtree(target_dir)

    for agent_file in sorted(SRC_AGENTS.glob("*.yml")):
        agent = load_agent(agent_file)
        name = agent["name"]
        for t in tools:
            relative_path = TARGETS[t]["path"].format(name=name)
            output_path = GENERATED / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            rendered = render(t, agent)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(rendered)
            print(f"Gerado: {output_path.relative_to(ROOT)}")


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
