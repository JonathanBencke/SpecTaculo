# Exemplo de task para validar a esteira SpecTaculo

## Entrada para o orquestrador

```text
#42 Preciso de um endpoint REST em Python/Flask que receba um JSON com nome e email,
valide o email e salve em um arquivo CSV. Se o email for inválido, deve retornar
erro 400 com uma mensagem clara.
```

## Organização esperada

Como a entrada contém o ID `#42`, o SpecTaculo deve criar a pasta:

```
specs/GH-42/
```

## O que a esteira deve produzir

1. `specs/GH-42/TASK.md` com a fase atual e checklist.
2. `specs/GH-42/SPEC.md` contendo:
   - Escopo do endpoint (`POST /usuarios`)
   - Critérios de aceite (status 201, 400, formato do CSV)
   - Contrato da API (exemplo de request/response)
   - Decisões pendentes (ex: local do arquivo CSV, se não especificado)
3. `specs/GH-42/PLAN.md` com passos para implementar o Flask app, validação e testes manuais.
4. Código implementado (app Flask + testes básicos).
5. `specs/GH-42/TASK.md` finalizado com review.

## Decisão esperada para o usuário

O exemplo deixa em aberto o caminho do arquivo CSV. A esteira deve marcar isso
como decisão pendente e perguntar ao usuário antes de implementar.

## Exemplo com ID do Jira

```text
PROJ-456 Preciso refatorar o módulo de autenticação para usar JWT.
```

Neste caso, a pasta deve ser:

```
specs/PROJ-456/
```

## Exemplo sem ID

```text
Preciso de uma página de login com validação de campos.
```

Neste caso, o agente `spectaculo-intake` deve sugerir um nome como `pagina-login-validacao` e perguntar ao usuário se aceita, criando:

```
specs/pagina-login-validacao/
```
