# Exemplo de task para validar a esteira SpecTaculo

## Entrada para o orquestrador

```text
Preciso de um endpoint REST em Python/Flask que receba um JSON com nome e email,
valide o email e salve em um arquivo CSV. Se o email for inválido, deve retornar
erro 400 com uma mensagem clara.
```

## O que a esteira deve produzir

1. `TASK.md` com a fase atual e checklist.
2. `SPEC.md` contendo:
   - Escopo do endpoint (`POST /usuarios`)
   - Critérios de aceite (status 201, 400, formato do CSV)
   - Contrato da API (exemplo de request/response)
   - Decisões pendentes (ex: local do arquivo CSV, se não especificado)
3. `PLAN.md` com passos para implementar o Flask app, validação e testes manuais.
4. Código implementado (app Flask + testes básicos).
5. `TASK.md` finalizado com review.

## Decisão esperada para o usuário

O exemplo deixa em aberto o caminho do arquivo CSV. A esteira deve marcar isso
como decisão pendente e perguntar ao usuário antes de implementar.
