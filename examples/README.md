# Exemplo ponta-a-ponta

> Saída esperada ao rodar a esteira SpecTaculo sobre a task do
> [`example-task.md`](../example-task.md). Esta pasta é **referência visual**
> do que a esteira produz, não é executada automaticamente.

## Task de entrada

```text
#42 Preciso de um endpoint REST em Python/Flask que receba um JSON com nome e email,
valide o email e salve em um arquivo CSV. Se o email for inválido, deve retornar
erro 400 com uma mensagem clara.
```

## Organização esperada

Como a entrada contém o ID `#42` (GitHub), o `spectaculo-intake` cria:

```
specs/GH-42/
├── TASK.md
├── STATE.json
├── SPEC.md
└── PLAN.md
```

## Artefatos de referência

- [`TASK.md`](./GH-42/TASK.md) — todo-list central com fase, checklist,
  decisão pendente (caminho do CSV) e histórico de handoffs.
- [`STATE.json`](./GH-42/STATE.json) — estado persistente para resume
  (fase atual, contadores de tentativas dos loops).
- [`SPEC.md`](./GH-42/SPEC.md) — especificação formal (escopo, critérios
  de aceite, contrato da API).
- [`PLAN.md`](./GH-42/PLAN.md) — plano executável com passos ordenados.

## Decisão esperada para o usuário

O exemplo deixa em aberto o caminho do arquivo CSV. A esteira **deve parar**
no `spectaculo-validate` e marcar isso como `PENDING` até o usuário responder.
