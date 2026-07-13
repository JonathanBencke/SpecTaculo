# TASK: Endpoint Flask que recebe nome/email e salva em CSV

**Spec ID:** `GH-42`
**Spec Dir:** `specs/GH-42/`
**Fase atual:** `validate`
**Criado em:** `2026-07-13T12:00:00Z`

## Changelog detectado
- **Caminho:** `CHANGELOG.md`
- **Padrão:** Keep a Changelog
- **Status:** reconhecido

## Checklist da esteira
- [x] Intake validado
- [x] Spec escrita (`SPEC.md`)
- [ ] Spec aprovada (`validate` → APPROVE)
- [ ] Plano criado (`PLAN.md`)
- [ ] Execução (0/N passos concluídos)
- [ ] Review (`review` → APPROVE)
- [ ] Entrega finalizada

## Decisões pendentes
- **Pergunta:** Onde o arquivo CSV de usuários deve ser salvo (caminho absoluto)?
  - **Bloqueia:** sim
  - **Contexto:** A task original não especifica o diretório. Sugestões:
    `./data/usuarios.csv` ou um caminho via variável de ambiente `USUARIOS_CSV`.
- **Pergunta:** O CSV deve ser criado com cabeçalho na primeira execução?
  - **Bloqueia:** não
  - **Contexto:** Convenção comum, mas não explicitado.

## Histórico de handoffs
- `[intake] APPROVE — próximo: spectaculo-spec — artefatos: TASK.md, STATE.json`
- `[spec] APPROVE — próximo: spectaculo-validate — artefatos: SPEC.md, TASK.md`
- `[validate] PENDING — próximo: humano — artefatos: TASK.md — questões: caminho do CSV`

## Bloqueios
- Aguardando resposta do usuário sobre o caminho do CSV (crítico).

> _Referência estrutural: `src/templates/task.md.j2`_
