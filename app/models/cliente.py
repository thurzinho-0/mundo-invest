# =============================================================================
# MUNDO INVEST — Model ORM: Cliente
# =============================================================================
# Representa a tabela "clientes" no banco de dados.
# Cada registro armazena dados do cliente, seu patrimônio e o status
# do processo (espelhando o ciclo de vida do card no Pipefy).
# =============================================================================

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.db.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    # Chave primária autoincremental
    id = Column(Integer, primary_key=True, index=True)

    # Dados básicos do cliente
    nome = Column(String(200), nullable=False)
    email = Column(String(254), unique=True, index=True, nullable=False)

    # Tipo da solicitação cadastrada (ex: "Atualização cadastral")
    tipo_solicitacao = Column(String(200), nullable=False)

    # Patrimônio investido em reais — usado para calcular prioridade
    valor_patrimonio = Column(Float, nullable=False)

    # Status atual do processo:
    #   "Aguardando Análise" → estado inicial ao criar o cliente
    #   "Processado"         → após receber e processar o webhook do Pipefy
    status = Column(String(50), nullable=False, default="Aguardando Análise")

    # Prioridade definida pela regra de negócio ao processar o webhook:
    #   "prioridade_alta"   → patrimônio >= 200.000
    #   "prioridade_normal" → patrimônio < 200.000
    #   None                → ainda não processado
    prioridade = Column(String(50), nullable=True)

    # ID do card criado no Pipefy (simulado localmente)
    pipefy_card_id = Column(String(100), nullable=True)

    # Timestamps de auditoria
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self):
        return f"<Cliente id={self.id} email={self.email} status={self.status}>"
