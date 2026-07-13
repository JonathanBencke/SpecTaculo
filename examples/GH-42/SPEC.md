# SPEC: Endpoint Flask que recebe nome/email e salva em CSV

## Escopo
**Incluído:**
- Endpoint HTTP `POST /usuarios` que recebe JSON com `nome` e `email`.
- Validação do formato do email.
- Persistência dos registros válidos em um arquivo CSV.
- Resposta HTTP 201 em caso de sucesso e 400 em caso de email inválido.

**Fora de escopo:**
- Autenticação/autorização.
- Persistência em banco de dados relacional.
- Listagem/remoção de usuários (apenas criação).

## Critérios de aceite
- `POST /usuarios` com `{"nome": "...", "email": "user@host.com"}` retorna `201`
  e o registro é anexado ao CSV.
- `POST /usuarios` com email inválido retorna `400` com `{"erro": "email inválido"}`,
  e nada é escrito no CSV.
- O CSV possui cabeçalho `nome,email` (decisão pendente confirma).
- Campos ausentes no JSON retornam `400` com mensagem clara.
- O endpoint aceita apenas `Content-Type: application/json`.

## Contratos e interfaces

**Request**
```http
POST /usuarios HTTP/1.1
Content-Type: application/json

{"nome": "Ana", "email": "ana@example.com"}
```

**Response 201**
```json
{"id": "<linha-do-csv>", "nome": "Ana", "email": "ana@example.com"}
```

**Response 400**
```json
{"erro": "email inválido"}
```

**Erros conhecidos:**
- `400` — JSON malformado, campos ausentes, email inválido.
- `500` — falha de I/O ao escrever no CSV (não recuperável pelo cliente).

## Restrições e premissas
- Stack: Python 3.11+, Flask.
- O arquivo CSV é um recurso append-only; não há locking explícito
  (premissa: concorrência baixa).
- A validação de email usa regex simples (não há envio de confirmação).

## Decisões pendentes
- **Caminho do CSV:** não definido. Sugestões: `./data/usuarios.csv` ou via
  variável de ambiente `USUARIOS_CSV`. **Bloqueia implementação.**
- **Cabeçalho do CSV:** incluir `nome,email` na primeira criação do arquivo?

> _Bloco `## Handoff` do spectaculo-spec:_
> - **Fase:** spec
> - **Status:** APPROVE
> - **Próximo:** spectaculo-validate
> - **Artefatos:** `SPEC.md`, `TASK.md`
> - **Questões em aberto:** caminho do CSV, cabeçalho.
