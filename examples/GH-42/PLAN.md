# PLAN: Endpoint Flask que recebe nome/email e salva em CSV

## Objetivo
- Entregar um app Flask com `POST /usuarios` que valida email e salva em CSV,
  com testes cobrindo os casos de sucesso e erro.

## Dependências externas
- Resposta do usuário sobre o **caminho do CSV** (decisão pendente bloqueante).
- Definição sobre cabeçalho do CSV (decisão pendente não-bloqueante).

## Passos
1. [ ] Inicializar projeto Flask + `requirements.txt` -> produz `app.py`, `requirements.txt`
2. [ ] Implementar helper de validação de email -> modifica `app.py`
3. [ ] Implementar escrita append-only no CSV (com cabeçalho condicional) -> modifica `app.py`
4. [ ] Implementar rota `POST /usuarios` com tratamento de erros 400/500 -> modifica `app.py`
5. [ ] Escrever testes para 201, 400 (email inválido), 400 (campos ausentes) -> produz `test_app.py`
6. [ ] Documentar como rodar (env `USUARIOS_CSV`, `flask run`) -> modifica `README.md`
7. [ ] Atualizar `CHANGELOG.md` com a entrada da mudança -> modifica `CHANGELOG.md`

## Critério de conclusão
- Todos os testes passam localmente.
- `POST /usuarios` atende aos critérios de aceite da `SPEC.md`.
- `CHANGELOG.md` atualizado no padrão Keep a Changelog.
- `TASK.md` e `STATE.json` marcados com `review → APPROVE`.

> _Bloco `## Handoff` do spectaculo-plan:_
> - **Fase:** plan
> - **Status:** APPROVE
> - **Próximo:** spectaculo-execute
> - **Artefatos:** `PLAN.md`, `TASK.md`
> - **Questões em aberto:** caminho do CSV (bloqueante).
