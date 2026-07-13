# Schema dos agentes (`AgentSpec`)

> Referência formal dos campos aceitos por cada YAML em `src/agents/*.yml`.
> A autoridade é o modelo pydantic em [`src/schema.py`](../src/schema.py).
> Qualquer campo não listado aqui é **rejeitado** (`extra: forbid`).

## Campos

| Campo         | Tipo                         | Obrigatório | Default     | Descrição                                                                  |
|---------------|------------------------------|-------------|-------------|----------------------------------------------------------------------------|
| `name`        | `str`                        | sim         | —           | Identificador único em **kebab-case**. Regex: `^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$`. |
| `description` | `str`                        | sim         | —           | Resumo curto (não-vazio) do papel do agente.                               |
| `entry`       | `str`                        | sim         | —           | O que o agente recebe como entrada.                                        |
| `output`      | `str`                        | sim         | —           | O que o agente produz.                                                     |
| `rules`       | `list[str]`                  | não         | `[]`        | Regras/constraints. Entradas vazias ou só-whitespace são rejeitadas.       |
| `prompt`      | `str`                        | sim         | —           | Corpo do prompt executado. Pode conter placeholders Jinja (ex.: `{{ user_input }}`). |
| `mode`        | `"primary" \| "subagent"`    | não         | `"subagent"`| Papel na CLI. Só `spectaculo-run` usa `"primary"`.                         |
| `tools`       | `list[str] \| null`          | não         | `null`      | Override das ferramentas permitidas (usado pelo template opencode/kiro).   |

## Exemplo mínimo

```yaml
name: spectaculo-exemplo
description: Agente de demonstração.
entry: Texto livre descrevendo a tarefa.
output: Arquivo de saída com o resultado.
rules:
  - Primeira regra.
  - "Regra com dois-pontos: deve ser quoted."
prompt: |
  Você é o agente **spectaculo-exemplo**.
  ## Entrada
  {{ user_input }}
  ## Saída esperada
  - Resultado processado
  ## Handoff
  - **Fase:** exemplo
  - **Status:** APPROVE | PENDING | BLOCKED
```

## Validações aplicadas

1. **`name`** em kebab-case (minúsculas, dígitos, hífens; sem underline, sem
   iniciar com hífen/dígito, sem hífen duplo).
2. **`rules`** sem entradas vazias ou só-whitespace (aplica `strip()`).
3. **`mode`** só aceita `"primary"` ou `"subagent"`.
4. **`extra: forbid`** — qualquer campo não-schema invalida o YAML.

## Como adicionar um novo campo

1. Adicione-o a `src/schema.py` (`AgentSpec`).
2. Atualize esta tabela.
3. Se afetar a renderização, ajuste os templates em `src/templates/`.
4. Adicione teste em `tests/test_schema.py`.
5. Rode `python src/generate.py all --clean` e `pytest tests/ -v`.

## Placeholders Jinja nos prompts

Os prompts são texto puro e podem conter placeholders `{{ ... }}`. Atualmente
apenas `spectaculo-run` e `spectaculo-intake` usam `{{ user_input }}`, que é
substituído pela CLI no momento da invocação (não durante a geração).

O contexto de renderização do template (`src/generate.py::render`) recebe:

- todos os campos do `AgentSpec` via `model_dump()`;
- `tool` — a CLI alvo (`claude`, `kimi`, `opencode`, `kiro`), usada para
  injetar o bloco de **Dispatch específico da CLI** no orquestrador.
