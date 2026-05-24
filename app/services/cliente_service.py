# =============================================================================
# MUNDO INVEST — Service: Clientes
# =============================================================================
# Camada de serviço que concentra toda a lógica de negócio relacionada
# a clientes. Os roteadores (API layer) chamam estas funções, que por sua
# vez orquestram banco de dados + integração com o Pipefy.
#
# Separar a lógica aqui (e não dentro dos roteadores) facilita:
#   - Testes unitários sem levantar o servidor HTTP
#   - Reutilização em outros contextos (CLI, workers, etc.)
# =============================================================================

import os
import logging
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.evento import EventoWebhook
from app.schemas.schemas import ClienteCreate, WebhookCardUpdated
from app.pipefy.client import criar_card_pipefy, atualizar_card_pipefy

logger = logging.getLogger(__name__)

# ID do pipe no Pipefy — em produção viria de variável de ambiente
PIPEFY_PIPE_ID = os.getenv("PIPEFY_PIPE_ID", "pipe_mundo_invest_001")

# Limiar de patrimônio que define alta prioridade (R$ 200.000,00)
LIMIAR_PRIORIDADE_ALTA = 200_000.0


# ---------------------------------------------------------------------------
# Serviço: Criação de cliente
# ---------------------------------------------------------------------------
def criar_cliente(db: Session, dados: ClienteCreate) -> Cliente:
    """
    Fluxo completo de criação de um novo cliente:
      1. Verifica se o e-mail já está cadastrado (evita duplicatas)
      2. Persiste o cliente no banco com status "Aguardando Análise"
      3. Simula o envio da mutation createCard para o Pipefy
      4. Atualiza o registro com o pipefy_card_id retornado

    Lança ValueError se o e-mail já existir.
    """

    # --- 1. Verificação de duplicidade por e-mail ---
    cliente_existente = db.query(Cliente).filter(
        Cliente.email == dados.cliente_email
    ).first()

    if cliente_existente:
        raise ValueError(f"Já existe um cliente com o e-mail '{dados.cliente_email}'")

    # --- 2. Persistência no banco local ---
    novo_cliente = Cliente(
        nome=dados.cliente_nome,
        email=dados.cliente_email,
        tipo_solicitacao=dados.tipo_solicitacao,
        valor_patrimonio=dados.valor_patrimonio,
        status="Aguardando Análise",  # Status inicial conforme especificação
    )
    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)  # Recarrega para obter o id gerado

    logger.info(
        "Cliente criado com sucesso: id=%s | email=%s",
        novo_cliente.id, novo_cliente.email,
    )

    # --- 3. Envio (simulado) da mutation createCard ao Pipefy ---
    resposta_pipefy = criar_card_pipefy(
        pipe_id=PIPEFY_PIPE_ID,
        cliente_nome=dados.cliente_nome,
        cliente_email=dados.cliente_email,
        valor_patrimonio=dados.valor_patrimonio,
    )

    # --- 4. Salva o card_id retornado pelo Pipefy no banco local ---
    card_id = resposta_pipefy["data"]["createCard"]["card"]["id"]
    novo_cliente.pipefy_card_id = card_id
    db.commit()
    db.refresh(novo_cliente)

    logger.info(
        "Card Pipefy vinculado: cliente_id=%s | pipefy_card_id=%s",
        novo_cliente.id, card_id,
    )

    return novo_cliente


# ---------------------------------------------------------------------------
# Serviço: Processamento de webhook de card atualizado
# ---------------------------------------------------------------------------
def processar_webhook_card_updated(db: Session, dados: WebhookCardUpdated) -> dict:
    """
    Fluxo de processamento do webhook:
      1. Idempotência: verifica se o event_id já foi processado
      2. Localiza o cliente pelo e-mail
      3. Aplica regra de negócio para definir prioridade
      4. Simula o envio da mutation updateCardField ao Pipefy
      5. Atualiza o banco local com novo status e prioridade

    Retorna um dicionário com o resultado do processamento.
    Lança:
      - ValueError("duplicado") se o event_id já foi processado
      - ValueError("nao_encontrado") se o cliente não existir no banco
    """

    # --- 1. Verificação de idempotência ---
    # Buscamos o event_id na tabela de eventos processados
    evento_existente = db.query(EventoWebhook).filter(
        EventoWebhook.event_id == dados.event_id
    ).first()

    if evento_existente:
        logger.warning(
            "Evento duplicado ignorado: event_id=%s", dados.event_id
        )
        raise ValueError("duplicado")

    # --- 2. Localiza o cliente no banco pelo e-mail ---
    cliente = db.query(Cliente).filter(
        Cliente.email == dados.cliente_email
    ).first()

    if not cliente:
        logger.error(
            "Cliente não encontrado para o webhook: email=%s", dados.cliente_email
        )
        raise ValueError("nao_encontrado")

    # --- 3. Regra de negócio: cálculo de prioridade ---
    # Patrimônio >= 200.000 → prioridade_alta
    # Patrimônio <  200.000 → prioridade_normal
    if cliente.valor_patrimonio >= LIMIAR_PRIORIDADE_ALTA:
        prioridade = "prioridade_alta"
    else:
        prioridade = "prioridade_normal"

    logger.info(
        "Prioridade definida: email=%s | patrimônio=%.2f | prioridade=%s",
        cliente.email, cliente.valor_patrimonio, prioridade,
    )

    # --- 4. Envio (simulado) da mutation updateCardField ao Pipefy ---
    card_id = cliente.pipefy_card_id or dados.card_id
    atualizar_card_pipefy(
        card_id=card_id,
        novo_status="Processado",
        prioridade=prioridade,
    )

    # --- 5. Atualiza o banco local ---
    cliente.status = "Processado"
    cliente.prioridade = prioridade

    # Registra o evento para garantir idempotência em chamadas futuras
    novo_evento = EventoWebhook(
        event_id=dados.event_id,
        card_id=dados.card_id,
        cliente_email=dados.cliente_email,
        timestamp_evento=dados.timestamp,
    )
    db.add(novo_evento)
    db.commit()

    logger.info(
        "Webhook processado com sucesso: event_id=%s | cliente_id=%s",
        dados.event_id, cliente.id,
    )

    return {
        "mensagem": "Evento processado com sucesso",
        "event_id": dados.event_id,
        "cliente_email": dados.cliente_email,
        "prioridade_definida": prioridade,
        "status_atualizado": "Processado",
    }
