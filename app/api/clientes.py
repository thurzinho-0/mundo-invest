# =============================================================================
# MUNDO INVEST — Roteador: /clientes
# =============================================================================
# Esta camada é responsável apenas por:
#   - Receber e validar a requisição HTTP
#   - Chamar a camada de serviço
#   - Retornar a resposta HTTP adequada
#
# Toda lógica de negócio fica em app/services/cliente_service.py
# =============================================================================

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.schemas import ClienteCreate, ClienteResponse
from app.services.cliente_service import criar_cliente

logger = logging.getLogger(__name__)

# Prefixo "/clientes" é definido em main.py ao incluir este roteador
router = APIRouter()


@router.post(
    "/",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo cliente",
    description=(
        "Valida os dados, persiste o cliente no banco com status "
        "'Aguardando Análise' e simula a criação de um card no Pipefy via GraphQL."
    ),
)
def endpoint_criar_cliente(
    dados: ClienteCreate,
    db: Session = Depends(get_db),
):
    """
    POST /clientes

    Payload esperado:
    {
        "cliente_nome": "João Silva",
        "cliente_email": "joao.silva@example.com",
        "tipo_solicitacao": "Atualização cadastral",
        "valor_patrimonio": 250000
    }
    """
    try:
        cliente = criar_cliente(db=db, dados=dados)
        return cliente

    except ValueError as e:
        # E-mail duplicado ou outro erro de validação de negócio
        logger.warning("Falha ao criar cliente: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    except Exception as e:
        # Erros inesperados — logamos e retornamos 500
        logger.exception("Erro inesperado ao criar cliente: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar a solicitação.",
        )
