# Mundo Invest — Client Management & Pipefy Integration API

> Teste técnico — Backend Developer  
> Sistema interno para gestão de clientes e integração com o Pipefy via GraphQL.

---

## Sumário

- [Visão Geral](#visão-geral)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Como Rodar Localmente](#como-rodar-localmente)
- [Rodando os Testes](#rodando-os-testes)
- [Exemplos de Requisição (curl)](#exemplos-de-requisição-curl)
- [As Mutations GraphQL do Pipefy](#as-mutations-graphql-do-pipefy)
- [Decisões de Arquitetura](#decisões-de-arquitetura)
- [Visão de Produção na AWS](#visão-de-produção-na-aws)

---

## Visão Geral

Esta API expõe dois fluxos principais:

**Fluxo 1 — `POST /clientes`**  
Recebe os dados de um novo cliente, valida, persiste no banco com status `"Aguardando Análise"` e simula o envio da mutation `createCard` para o Pipefy.

**Fluxo 2 — `POST /webhooks/pipefy/card-updated`**  
Simula o recebimento de um webhook do Pipefy. Garante idempotência via `event_id`, aplica a regra de prioridade por patrimônio e simula o envio da mutation `updateCardField` para atualizar o card no Pipefy.

---

## Estrutura de Pastas

```
mundo-invest/
├── app/
│   ├── main.py                  # Ponto de entrada: FastAPI + roteadores
│   ├── api/
│   │   ├── clientes.py          # Roteador POST /clientes
│   │   └── webhooks.py          # Roteador POST /webhooks/pipefy/card-updated
│   ├── services/
│   │   └── cliente_service.py   # LÓGICA DE NEGÓCIO (regras, orquestração)
│   ├── models/
│   │   ├── cliente.py           # ORM: tabela clientes
│   │   └── evento.py            # ORM: tabela eventos_webhook (idempotência)
│   ├── schemas/
│   │   └── schemas.py           # Pydantic: validação de entrada/saída
│   ├── pipefy/
│   │   └── client.py            # Mutations GraphQL reais do Pipefy (simulado)
│   └── db/
│       └── database.py          # Engine SQLAlchemy + get_db
├── tests/
│   ├── conftest.py              # Fixtures compartilhadas (banco de teste)
│   └── test_api.py              # 11 testes cobrindo os 3 cenários obrigatórios
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

### Separação de responsabilidades

```
Requisição HTTP
    ↓
app/api/          ← Recebe, valida formato (Pydantic), devolve HTTP
    ↓
app/services/     ← Regras de negócio, orquestração, lógica de prioridade
    ↓
app/pipefy/       ← Monta e "envia" mutations GraphQL para o Pipefy
app/db/           ← Persistência via SQLAlchemy
```

Essa separação garante que as regras de negócio em `services/` possam ser testadas independentemente sem subir o servidor HTTP.

---

## Tecnologias Utilizadas

| Tecnologia | Papel |
|---|---|
| **FastAPI** | Framework web — roteamento, validação, documentação automática |
| **SQLAlchemy** | ORM — mapeamento das tabelas e gerenciamento de sessões |
| **Pydantic v2** | Validação e serialização de dados de entrada/saída |
| **SQLite** | Banco de dados local (zero configuração para desenvolvimento) |
| **pytest + httpx** | Testes automatizados com client HTTP real |
| **uvicorn** | Servidor ASGI para rodar a aplicação |

---

## Como Rodar Localmente

### Pré-requisitos

- Python 3.10+
- pip

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/mundo-invest.git
cd mundo-invest
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
# Edite o .env se quiser usar PostgreSQL ou configurar o PIPEFY_PIPE_ID
```

### 5. Inicie o servidor

```bash
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`.

A documentação interativa (Swagger UI) estará em `http://localhost:8000/docs`.

---

## Rodando os Testes

```bash
# Todos os testes
pytest tests/ -v

# Com saída resumida
pytest tests/ -v --no-header

# Apenas um grupo de testes
pytest tests/ -v -k "TestCriacaoCliente"
pytest tests/ -v -k "TestWebhookPrioridade"
pytest tests/ -v -k "TestIdempotencia"
```

Saída esperada:

```
tests/test_api.py::TestCriacaoCliente::test_criar_cliente_sucesso          PASSED
tests/test_api.py::TestCriacaoCliente::test_email_duplicado_retorna_409    PASSED
tests/test_api.py::TestCriacaoCliente::test_email_invalido_retorna_422     PASSED
tests/test_api.py::TestCriacaoCliente::test_campo_ausente_retorna_422      PASSED
tests/test_api.py::TestCriacaoCliente::test_patrimonio_negativo_retorna_422 PASSED
tests/test_api.py::TestWebhookPrioridade::test_patrimonio_250k_prioridade_alta  PASSED
tests/test_api.py::TestWebhookPrioridade::test_patrimonio_200k_exato_prioridade_alta PASSED
tests/test_api.py::TestWebhookPrioridade::test_patrimonio_150k_prioridade_normal PASSED
tests/test_api.py::TestWebhookPrioridade::test_cliente_inexistente_retorna_404   PASSED
tests/test_api.py::TestIdempotencia::test_event_id_duplicado_retorna_200_sem_reprocessar PASSED
tests/test_api.py::TestIdempotencia::test_dois_event_ids_distintos_sao_aceitos   PASSED

11 passed in 0.59s
```

---

## Exemplos de Requisição (curl)

### Fluxo 1 — Criar cliente

```bash
curl -X POST http://localhost:8000/clientes/ \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_nome": "João Silva",
    "cliente_email": "joao.silva@example.com",
    "tipo_solicitacao": "Atualização cadastral",
    "valor_patrimonio": 250000
  }'
```

**Resposta esperada (201 Created):**

```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao.silva@example.com",
  "tipo_solicitacao": "Atualização cadastral",
  "valor_patrimonio": 250000.0,
  "status": "Aguardando Análise",
  "prioridade": null,
  "pipefy_card_id": "card_a3f9d1b2",
  "criado_em": "2026-05-22T10:00:00Z",
  "atualizado_em": "2026-05-22T10:00:00Z"
}
```

---

### Fluxo 2 — Webhook de card atualizado

```bash
curl -X POST http://localhost:8000/webhooks/pipefy/card-updated \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_123",
    "card_id": "card_a3f9d1b2",
    "cliente_email": "joao.silva@example.com",
    "timestamp": "2026-05-18T12:00:00Z"
  }'
```

**Resposta esperada (200 OK):**

```json
{
  "mensagem": "Evento processado com sucesso",
  "event_id": "evt_123",
  "cliente_email": "joao.silva@example.com",
  "prioridade_definida": "prioridade_alta",
  "status_atualizado": "Processado"
}
```

**Mesma chamada repetida (idempotência):**

```json
{
  "mensagem": "Evento já processado anteriormente (idempotente)",
  "event_id": "evt_123",
  "cliente_email": "joao.silva@example.com",
  "prioridade_definida": null,
  "status_atualizado": "sem alteração"
}
```

---

### Health check

```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "mundo-invest-api"}
```

---

## As Mutations GraphQL do Pipefy

Todas as mutations estão definidas em `app/pipefy/client.py` com comentários explicando a origem de cada uma.

### Mutation 1 — `createCard`

Fonte: [developers.pipefy.com/reference/mutations-cards#createcard](https://developers.pipefy.com/reference/mutations-cards#createcard)

```graphql
mutation CreateCard(
  $pipe_id: ID!,
  $title: String!,
  $email: String!,
  $patrimonio: String!
) {
  createCard(input: {
    pipe_id: $pipe_id
    title: $title
    fields_attributes: [
      { field_id: "cliente_email",    field_value: $email      }
      { field_id: "valor_patrimonio", field_value: $patrimonio }
    ]
  }) {
    card {
      id
      title
      current_phase { name }
    }
  }
}
```

### Mutation 2 — `updateCardField`

Fonte: [developers.pipefy.com/reference/mutations-cards#updatecardfield](https://developers.pipefy.com/reference/mutations-cards#updatecardfield)

```graphql
mutation UpdateCardField(
  $card_id: ID!,
  $field_id: String!,
  $new_value: String!
) {
  updateCardField(input: {
    card_id: $card_id
    field_id: $field_id
    new_value: $new_value
  }) {
    success
    card { id title }
  }
}
```

> Em produção, essa mutation seria chamada duas vezes por webhook: uma para atualizar o campo `status_cliente` e outra para `prioridade`.

---

## Decisões de Arquitetura

**Por que FastAPI?**  
Validação automática via Pydantic, documentação interativa embutida (Swagger/ReDoc), e suporte nativo a async — ideal para webhooks de alta frequência.

**Por que SQLite no desenvolvimento?**  
Zero configuração — basta rodar `uvicorn app.main:app`. Para produção, trocar `DATABASE_URL` por uma connection string do PostgreSQL/RDS é suficiente; o SQLAlchemy abstrai o restante.

**Idempotência via tabela `eventos_webhook`**  
Cada `event_id` processado é persistido. Antes de processar, consultamos essa tabela. Se o `event_id` já existir, retornamos 200 sem reprocessar. Em produção, essa tabela seria indexada por `event_id` (já está no código).

**Regra de prioridade isolada no service**  
A lógica `patrimônio >= 200.000 → prioridade_alta` vive exclusivamente em `app/services/cliente_service.py`. Isso facilita testes unitários sem depender de HTTP e permite alterar a regra sem tocar na camada de API.

---

## Visão de Produção na AWS

### Arquitetura sugerida

```
API Gateway
    ↓
Lambda (FastAPI via Mangum)   ←→   RDS PostgreSQL (clientes + eventos)
    ↓
SQS (fila de webhooks)
    ↓
Lambda Worker (processa webhooks da fila)
    ↓
DynamoDB (cache de event_ids para dedup rápido)
```

### Detalhamento por componente

**API Gateway + Lambda (Mangum)**  
A aplicação FastAPI roda sem alterações dentro de uma Lambda usando o adaptador [Mangum](https://mangum.io/). O API Gateway roteia `POST /clientes` e `POST /webhooks/*` para a Lambda correspondente. Escalabilidade automática sem gerenciar servidores.

**RDS PostgreSQL (Multi-AZ)**  
Substitui o SQLite local. O SQLAlchemy aponta para o endpoint do RDS via `DATABASE_URL`. Em ambiente de alta concorrência, usamos connection pooling via `pg_bouncer` ou RDS Proxy para não estourar o limite de conexões.

**SQS para webhooks**  
Em vez de processar o webhook de forma síncrona (o que poderia causar timeout se o Pipefy tiver um tempo máximo de espera), o endpoint de webhook publica o evento numa fila SQS e retorna 200 imediatamente. Uma Lambda separada consome a fila com retentativas automáticas em caso de falha — garantindo entrega ao menos uma vez.

**DynamoDB para idempotência**  
A tabela `eventos_webhook` no RDS funciona em baixo volume, mas sob alta concorrência pode gerar race conditions. O DynamoDB com operação condicional (`PutItem` com `ConditionExpression: attribute_not_exists(event_id)`) garante deduplicação atômica e com latência de milissegundos — sem travar o banco relacional.

**CloudWatch + X-Ray**  
Logs estruturados (já presentes no código via `logging`) são coletados pelo CloudWatch. O X-Ray instrumenta o tempo de cada chamada (banco, Pipefy, SQS) para facilitar debugging de latência em produção.

**Secrets Manager**  
`PIPEFY_TOKEN` e credenciais do banco nunca ficam em variáveis de ambiente em texto puro — ficam no AWS Secrets Manager e são recuperadas pela Lambda na inicialização.
