# =============================================================================
# MUNDO INVEST — Schemas Pydantic (validação de entrada e saída)
# =============================================================================
# Pydantic valida e documenta automaticamente os payloads da API.
# Separamos os schemas de entrada (request) e saída (response) para
# não expor campos internos desnecessariamente.
# =============================================================================

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


# ---------------------------------------------------------------------------
# CLIENTES
# ---------------------------------------------------------------------------

class ClienteCreate(BaseModel):
    """
    Payload esperado no POST /clientes.
    Todos os campos são obrigatórios.
    """
    cliente_nome: str
    cliente_email: EmailStr          # Pydantic valida o formato do e-mail automaticamente
    tipo_solicitacao: str
    valor_patrimonio: float

    # Validação extra: patrimônio não pode ser negativo
    @field_validator("valor_patrimonio")
    @classmethod
    def patrimonio_deve_ser_positivo(cls, v: float) -> float:
        if v < 0:
            raise ValueError("valor_patrimonio não pode ser negativo")
        return v

    # Validação extra: nome não pode ser string vazia
    @field_validator("cliente_nome")
    @classmethod
    def nome_nao_pode_ser_vazio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("cliente_nome não pode ser vazio")
        return v.strip()


class ClienteResponse(BaseModel):
    """
    Resposta retornada após criação ou consulta de um cliente.
    Inclui o pipefy_card_id simulado para rastreabilidade.
    """
    id: int
    nome: str
    email: str
    tipo_solicitacao: str
    valor_patrimonio: float
    status: str
    prioridade: Optional[str]
    pipefy_card_id: Optional[str]
    criado_em: datetime
    atualizado_em: datetime

    # Habilita a leitura direta de objetos ORM (modo "from_attributes")
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# WEBHOOKS
# ---------------------------------------------------------------------------

class WebhookCardUpdated(BaseModel):
    """
    Payload simulado de webhook enviado pelo Pipefy quando um card é atualizado.
    """
    event_id: str          # Identificador único do evento (chave de idempotência)
    card_id: str           # ID do card no Pipefy
    cliente_email: EmailStr
    timestamp: str         # ISO 8601 — ex: "2026-05-18T12:00:00Z"


class WebhookResponse(BaseModel):
    """
    Resposta retornada após processar o webhook.
    """
    mensagem: str
    event_id: str
    cliente_email: str
    prioridade_definida: Optional[str]
    status_atualizado: str
