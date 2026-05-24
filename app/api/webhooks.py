# =============================================================================
# MUNDO INVEST — Roteador: /webhooks
# =============================================================================
# Recebe eventos simulados do Pipefy (card atualizado) e delega o
# processamento para a camada de serviço.
# =============================================================================

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.schemas import WebhookCardUpdated, WebhookResponse
from app.services.cliente_service import processar_webhook_card_updated

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/pipefy/card-updated",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Simula recebimento de webhook do Pipefy",
    description=(
        "Processa o evento de atualização de card. "
        "Garante idempotência via event_id e aplica regra de prioridade por patrimônio."
    ),
)
def endpoint_webhook_card_updated(
    dados: WebhookCardUpdated,
    db: Session = Depends(get_db),
):
    """
    POST /webhooks/pipefy/card-updated

    Payload esperado:
    {
        "event_id": "evt_123",
        "card_id": "card_456",
        "cliente_email": "joao.silva@example.com",
        "timestamp": "2026-05-18T12:00:00Z"
    }
    """
    try:
        resultado = processar_webhook_card_updated(db=db, dados=dados)
        return resultado

    except ValueError as e:
        erro = str(e)

        if erro == "duplicado":
            # Evento já processado — retornamos 200 (idempotente, não é erro)
            logger.info("Evento duplicado recebido: event_id=%s", dados.event_id)
            return WebhookResponse(
                mensagem="Evento já processado anteriormente (idempotente)",
                event_id=dados.event_id,
                cliente_email=dados.cliente_email,
                prioridade_definida=None,
                status_atualizado="sem alteração",
            )

        if erro == "nao_encontrado":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente com e-mail '{dados.cliente_email}' não encontrado.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=erro,
        )

    except Exception as e:
        logger.exception("Erro inesperado ao processar webhook: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar o webhook.",
        )
