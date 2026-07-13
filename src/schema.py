"""
Schema de validação dos agentes SpecTaculo.

Cada agente é definido em YAML sob src/agents/<nome>.yml e deve satisfazer
este modelo antes de ser renderizado para qualquer CLI. A validação evita
que YAMLs malformados quebrem o build silenciosamente.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


# IDs de agente em kebab-case (ex: spectaculo-run, spectaculo-intake).
_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


class AgentSpec(BaseModel):
    """Modelo canônico de um agente da esteira SpecTaculo."""

    name: str = Field(..., description="Identificador único em kebab-case.")
    description: str = Field(..., min_length=1, description="Resumo curto do papel.")
    entry: str = Field(..., min_length=1, description="O que o agente recebe.")
    output: str = Field(..., min_length=1, description="O que o agente produz.")
    rules: List[str] = Field(
        default_factory=list, description="Regras constraints do agente."
    )
    prompt: str = Field(..., min_length=1, description="Corpo do prompt executado.")
    mode: Literal["primary", "subagent"] = Field(
        default="subagent",
        description="Papel do agente na CLI (orquestrador=primary, demais=subagent).",
    )
    tools: Optional[List[str]] = Field(
        default=None,
        description="Lista de ferramentas permitidas (override do default da CLI).",
    )

    model_config = {"extra": "forbid"}

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        if not _NAME_RE.match(value):
            raise ValueError(
                f"Nome inválido '{value}'. Use kebab-case (ex: spectaculo-run)."
            )
        return value

    @field_validator("rules")
    @classmethod
    def _strip_rules(cls, value: List[str]) -> List[str]:
        stripped = [r.strip() for r in value if r and r.strip()]
        if len(stripped) != len(value):
            raise ValueError("Regras não podem ser vazias ou apenas whitespace.")
        return stripped

    @model_validator(mode="after")
    def _validate_prompt_uses_placeholders(self) -> "AgentSpec":
        # Agente orquestrador recebe entrada do usuário via {{ user_input }}.
        # Não exigimos em todos, mas se presente, sinalizamos que será renderizado.
        return self

    @classmethod
    def from_yaml(cls, path: Path) -> "AgentSpec":
        """Carrega e valida um agente a partir de um arquivo YAML."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)
