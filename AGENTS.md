# AGENTS.md

> Guia para agentes de IA (e humanos) que vão modificar este repositório.

Este repositório é o **gerador** do SpecTaculo, não um projeto qualquer que
*usa* o SpecTaculo. Ou seja: a maior parte do trabalho aqui é mexer em
`src/agents/*.yml`, `src/templates/*.j2`, `src/generate.py` e `src/schema.py`,
depois regenerar os artefatos e validar com testes.

## Comandos essenciais

```powershell
# Ambiente (uma vez)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pip install -e .

# Regenerar todos os artefatos a partir das fontes YAML + templates
python src/generate.py all --clean
# equivalente ao entry point instalado:
spectaculo-generate all --clean

# Rodar testes (validam schema, geração, templates e regressões)
pytest tests/ -v
# com cobertura:
pytest tests/ --cov=src --cov-report=term-missing
```

No Linux/macOS:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt && pip install -e .
python src/generate.py all --clean
pytest tests/ -v
```

## Arquitetura (resumo)

```
src/agents/*.yml       Fonte única (YAML) de cada agente da esteira
src/templates/*.j2     Templates Jinja2 por CLI + body compartilhado
src/schema.py          Modelo pydantic AgentSpec (validação do YAML)
src/generate.py        Gerador que renderiza YAML+template -> generated/
generated/             Saída gitignored (claude/kimi/opencode/kiro)
tests/                 pytest (schema, generate, templates)
install.ps1/install.sh Instaladores multiplataforma
.github/workflows/     CI (testes) + Release (zip + sha256)
```

## Fonte única de verdade

- **Edite o YAML, nunca o `generated/`.** Artefatos em `generated/` são
  derivados e gitignored; são regenerados a partir de `src/agents/*.yml`.
- **Os 3 templates markdown (claude/kimi/opencode) são wrappers finos.**
  O corpo vive em `src/templates/_body.md.j2` (macro `body`). Não duplique
  conteúdo entre eles.
- **O schema `AgentSpec`** em `src/schema.py` é a autoridade sobre quais
  campos um agente pode ter (`extra: forbid`). Adicionar um campo novo
  exige editar o schema, senão o YAML é rejeitado.

## Convenções

- IDs de agente em **kebab-case** (`spectaculo-run`, validado por regex).
- Apenas `spectaculo-run` tem `mode: primary`; todos os demais são `subagent`.
- Todo agente deve emitir um bloco `## Handoff` estruturado ao final.
- Os loops `validate → spec` e `review → execute` têm limite de 3 tentativas
  (`attempts.validate` / `attempts.review` no `STATE.json`).
- Prompts em **português** (consistência com o restante do projeto).

## Antes de considerar pronto

1. `python src/generate.py all --clean` roda sem erros.
2. `pytest tests/` passa (62+ testes cobrem schema, geração, regressão do
   bug do `--clean` do kiro, dispatch por CLI, etc.).
3. Nenhum JSON do kiro inválido (CI valida isso).
4. Se mexeu no schema, atualize `docs/agent-schema.md`.
5. Se mexeu no fluxo da esteira, atualize `src/templates/task.md.j2` e
   `src/templates/state.json.j2` para refletirem a nova estrutura.
