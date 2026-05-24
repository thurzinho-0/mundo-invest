# =============================================================================
# MUNDO INVEST — Cliente GraphQL do Pipefy (simulado)
# =============================================================================
# Esta camada seria responsável por se comunicar com a API GraphQL do Pipefy.
# Em produção, as mutations abaixo seriam enviadas para:
#   https://api.pipefy.com/graphql
# com o header: Authorization: Bearer <PIPEFY_TOKEN>
#
# Referência oficial da documentação do Pipefy:
#   https://developers.pipefy.com/reference/mutations-cards
#
# Como este é um ambiente de teste, as funções SIMULAM o envio e retornam
# respostas fictícias, mas as strings GraphQL são 100% reais e válidas.
# =============================================================================

import logging
import uuid

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# MUTATION 1 — Criação de Card no Pipefy
# ---------------------------------------------------------------------------
# Fonte: https://developers.pipefy.com/reference/mutations-cards#createcard
#
# A mutation `createCard` cria um novo card dentro de um pipe específico.
# Cada campo do formulário é passado como um objeto dentro de `fields_attributes`,
# onde `field_id` é o identificador do campo configurado no pipe do Pipefy
# e `field_value` é o valor a ser preenchido.
#
# Variáveis necessárias:
#   $pipe_id     → ID do pipe onde o card será criado
#   $title       → Título do card (geralmente o nome do cliente)
#   $email       → E-mail do cliente (campo customizado do pipe)
#   $patrimonio  → Valor do patrimônio como string (campos do Pipefy são strings)
# ---------------------------------------------------------------------------
CREATE_CARD_MUTATION = """
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
      { field_id: "cliente_email",      field_value: $email       }
      { field_id: "valor_patrimonio",   field_value: $patrimonio  }
    ]
  }) {
    card {
      id
      title
      current_phase {
        name
      }
    }
  }
}
"""


# ---------------------------------------------------------------------------
# MUTATION 2 — Atualização de campo de um Card no Pipefy
# ---------------------------------------------------------------------------
# Fonte: https://developers.pipefy.com/reference/mutations-cards#updatecardfield
#
# A mutation `updateCardField` atualiza o valor de um campo específico
# de um card já existente. Deve ser chamada uma vez por campo a atualizar.
#
# Para atualizar status e prioridade, precisaríamos de duas chamadas
# (ou combinar com `updateCard` se o campo for nativo como `title`).
#
# Variáveis necessárias:
#   $card_id      → ID do card a ser atualizado
#   $field_id     → Identificador do campo a alterar (configurado no pipe)
#   $new_value    → Novo valor para o campo
# ---------------------------------------------------------------------------
UPDATE_CARD_FIELD_MUTATION = """
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
    card {
      id
      title
    }
  }
}
"""


# ---------------------------------------------------------------------------
# Função auxiliar: monta o payload GraphQL no formato esperado pela API REST
# ---------------------------------------------------------------------------
def _build_graphql_payload(query: str, variables: dict) -> dict:
    """
    Retorna o dicionário que seria serializado como JSON no body da requisição
    HTTP para https://api.pipefy.com/graphql
    """
    return {"query": query, "variables": variables}


# ---------------------------------------------------------------------------
# Serviço: simula a criação de card no Pipefy
# ---------------------------------------------------------------------------
def criar_card_pipefy(
    pipe_id: str,
    cliente_nome: str,
    cliente_email: str,
    valor_patrimonio: float,
) -> dict:
    """
    Monta e 'envia' (simulado) a mutation createCard para o Pipefy.

    Em produção, aqui entraria algo como:
        import httpx
        response = httpx.post(
            "https://api.pipefy.com/graphql",
            json=payload,
            headers={"Authorization": f"Bearer {PIPEFY_TOKEN}"}
        )
        return response.json()

    Retorna um dicionário simulando a resposta do Pipefy.
    """
    # Patrimônio é convertido para string pois campos do Pipefy são tipados como string
    patrimonio_str = str(valor_patrimonio)

    # Monta o payload real que seria enviado ao Pipefy
    payload = _build_graphql_payload(
        query=CREATE_CARD_MUTATION,
        variables={
            "pipe_id": pipe_id,
            "title": cliente_nome,
            "email": cliente_email,
            "patrimonio": patrimonio_str,
        },
    )

    # Log do payload para fins de debug e auditoria
    logger.info(
        "[PIPEFY SIMULADO] createCard — payload GraphQL:\n"
        "pipe_id=%s | title=%s | email=%s | patrimônio=%s",
        pipe_id, cliente_nome, cliente_email, patrimonio_str,
    )
    logger.debug("[PIPEFY SIMULADO] Query completa: %s", payload)

    # -----------------------------------------------------------------------
    # SIMULAÇÃO: retornamos uma resposta fictícia no mesmo formato que
    # o Pipefy retornaria em produção
    # -----------------------------------------------------------------------
    card_id_simulado = f"card_{uuid.uuid4().hex[:8]}"
    return {
        "data": {
            "createCard": {
                "card": {
                    "id": card_id_simulado,
                    "title": cliente_nome,
                    "current_phase": {"name": "Aguardando Análise"},
                }
            }
        }
    }


# ---------------------------------------------------------------------------
# Serviço: simula a atualização de campos do card no Pipefy
# ---------------------------------------------------------------------------
def atualizar_card_pipefy(
    card_id: str,
    novo_status: str,
    prioridade: str,
) -> dict:
    """
    Monta e 'envia' (simulado) a mutation updateCardField para o Pipefy.
    São duas chamadas: uma para o campo 'status' e outra para 'prioridade'.

    Em produção, cada chamada seria um POST separado (ou poderia usar
    batch requests se o Pipefy suportar).

    Retorna um dicionário simulando as respostas do Pipefy.
    """
    # --- Payload para atualizar o status do card ---
    payload_status = _build_graphql_payload(
        query=UPDATE_CARD_FIELD_MUTATION,
        variables={
            "card_id": card_id,
            "field_id": "status_cliente",   # ID do campo configurado no pipe
            "new_value": novo_status,
        },
    )

    # --- Payload para atualizar a prioridade do card ---
    payload_prioridade = _build_graphql_payload(
        query=UPDATE_CARD_FIELD_MUTATION,
        variables={
            "card_id": card_id,
            "field_id": "prioridade",       # ID do campo configurado no pipe
            "new_value": prioridade,
        },
    )

    logger.info(
        "[PIPEFY SIMULADO] updateCardField — card_id=%s | status=%s | prioridade=%s",
        card_id, novo_status, prioridade,
    )
    logger.debug(
        "[PIPEFY SIMULADO] Payload status: %s | Payload prioridade: %s",
        payload_status, payload_prioridade,
    )

    # -----------------------------------------------------------------------
    # SIMULAÇÃO: retornamos resposta fictícia confirmando o sucesso
    # -----------------------------------------------------------------------
    return {
        "status_update": {
            "data": {"updateCardField": {"success": True, "card": {"id": card_id}}}
        },
        "prioridade_update": {
            "data": {"updateCardField": {"success": True, "card": {"id": card_id}}}
        },
    }
