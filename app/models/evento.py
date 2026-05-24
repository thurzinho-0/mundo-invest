# =============================================================================
# MUNDO INVEST — Model ORM: EventoWebhook
# =============================================================================
# Registra cada evento de webhook recebido para garantir IDEMPOTÊNCIA.
# Antes de processar um evento, verificamos se o event_id já existe aqui.
# Se existir, retornamos 200 sem reprocessar (evita duplicatas).
# =============================================================================

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.db.database import Base


class EventoWebhook(Base):
    __tablename__ = "eventos_webhook"

    # Chave primária autoincremental
    id = Column(Integer, primary_key=True, index=True)

    # Identificador único do evento enviado pelo Pipefy — é a chave de idempotência
    event_id = Column(String(100), unique=True, index=True, nullable=False)

    # ID do card no Pipefy referenciado pelo evento
    card_id = Column(String(100), nullable=False)

    # E-mail do cliente associado ao card
    cliente_email = Column(String(254), nullable=False)

    # Timestamp original do evento (enviado no payload)
    timestamp_evento = Column(String(50), nullable=False)

    # Quando registramos o evento em nosso sistema
    processado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<EventoWebhook event_id={self.event_id} card_id={self.card_id}>"
