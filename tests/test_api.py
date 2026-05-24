# =============================================================================
# MUNDO INVEST — Testes automatizados
# =============================================================================
# Cobre os 3 cenários obrigatórios:
#   1. Criação de cliente com payload válido
#   2. Regra de prioridade baseada no patrimônio
#   3. Bloqueio de event_id duplicado (idempotência)
# =============================================================================

# Payloads de teste reutilizáveis

CLIENTE_PADRAO = {
    "cliente_nome": "João Silva",
    "cliente_email": "joao.silva@example.com",
    "tipo_solicitacao": "Atualização cadastral",
    "valor_patrimonio": 250000,
}

CLIENTE_BAIXO = {
    "cliente_nome": "Maria Souza",
    "cliente_email": "maria.souza@example.com",
    "tipo_solicitacao": "Abertura de conta",
    "valor_patrimonio": 150000,
}

WEBHOOK = {
    "event_id": "evt_001",
    "card_id": "card_abc",
    "cliente_email": "joao.silva@example.com",
    "timestamp": "2026-05-18T12:00:00Z",
}


# =============================================================================
# TESTE 1 — Criação de cliente
# =============================================================================

class TestCriacaoCliente:

    def test_criar_cliente_sucesso(self, client):
        """Payload válido: 201 + status 'Aguardando Análise' + card_id."""
        r = client.post("/clientes/", json=CLIENTE_PADRAO)
        assert r.status_code == 201, r.text
        d = r.json()
        assert d["email"] == CLIENTE_PADRAO["cliente_email"]
        assert d["status"] == "Aguardando Análise"
        assert d["pipefy_card_id"] is not None and d["pipefy_card_id"].startswith("card_")

    def test_email_duplicado_retorna_409(self, client):
        """Dois cadastros com mesmo e-mail: segundo deve retornar 409."""
        client.post("/clientes/", json=CLIENTE_PADRAO)
        r = client.post("/clientes/", json=CLIENTE_PADRAO)
        assert r.status_code == 409

    def test_email_invalido_retorna_422(self, client):
        """E-mail inválido: 422."""
        r = client.post("/clientes/", json={**CLIENTE_PADRAO, "cliente_email": "nao@email"})
        assert r.status_code == 422

    def test_campo_ausente_retorna_422(self, client):
        """Sem valor_patrimonio: 422."""
        payload = {k: v for k, v in CLIENTE_PADRAO.items() if k != "valor_patrimonio"}
        assert client.post("/clientes/", json=payload).status_code == 422

    def test_patrimonio_negativo_retorna_422(self, client):
        """Patrimônio negativo: 422."""
        assert client.post("/clientes/", json={**CLIENTE_PADRAO, "valor_patrimonio": -500}).status_code == 422


# =============================================================================
# TESTE 2 — Regra de prioridade pelo patrimônio
# =============================================================================

class TestWebhookPrioridade:

    def _criar(self, c, payload=None):
        r = c.post("/clientes/", json=payload or CLIENTE_PADRAO)
        assert r.status_code == 201, r.text

    def test_patrimonio_250k_prioridade_alta(self, client):
        """250.000 >= 200.000 → prioridade_alta."""
        self._criar(client)
        r = client.post("/webhooks/pipefy/card-updated", json=WEBHOOK)
        assert r.status_code == 200, r.text
        assert r.json()["prioridade_definida"] == "prioridade_alta"
        assert r.json()["status_atualizado"] == "Processado"

    def test_patrimonio_200k_exato_prioridade_alta(self, client):
        """200.000 exato (limite inclusivo) → prioridade_alta."""
        self._criar(client, {**CLIENTE_PADRAO, "valor_patrimonio": 200000})
        r = client.post("/webhooks/pipefy/card-updated", json=WEBHOOK)
        assert r.status_code == 200
        assert r.json()["prioridade_definida"] == "prioridade_alta"

    def test_patrimonio_150k_prioridade_normal(self, client):
        """150.000 < 200.000 → prioridade_normal."""
        self._criar(client, CLIENTE_BAIXO)
        wh = {**WEBHOOK, "event_id": "evt_002", "cliente_email": CLIENTE_BAIXO["cliente_email"]}
        r = client.post("/webhooks/pipefy/card-updated", json=wh)
        assert r.status_code == 200
        assert r.json()["prioridade_definida"] == "prioridade_normal"

    def test_cliente_inexistente_retorna_404(self, client):
        """Webhook para e-mail que não existe no banco → 404."""
        wh = {**WEBHOOK, "cliente_email": "x@example.com"}
        assert client.post("/webhooks/pipefy/card-updated", json=wh).status_code == 404


# =============================================================================
# TESTE 3 — Idempotência
# =============================================================================

class TestIdempotencia:

    def test_event_id_duplicado_retorna_200_sem_reprocessar(self, client):
        """Mesmo event_id duas vezes → segundo retorna 200 com mensagem de duplicata."""
        client.post("/clientes/", json=CLIENTE_PADRAO)
        client.post("/webhooks/pipefy/card-updated", json=WEBHOOK)

        r = client.post("/webhooks/pipefy/card-updated", json=WEBHOOK)
        assert r.status_code == 200, r.text
        assert "já processado" in r.json()["mensagem"].lower()
        assert r.json()["status_atualizado"] == "sem alteração"

    def test_dois_event_ids_distintos_sao_aceitos(self, client):
        """Dois event_ids diferentes → ambos processados normalmente."""
        client.post("/clientes/", json=CLIENTE_PADRAO)
        r1 = client.post("/webhooks/pipefy/card-updated", json=WEBHOOK)
        assert r1.status_code == 200
        r2 = client.post("/webhooks/pipefy/card-updated", json={**WEBHOOK, "event_id": "evt_999"})
        assert r2.status_code == 200
        assert r2.json()["event_id"] == "evt_999"
