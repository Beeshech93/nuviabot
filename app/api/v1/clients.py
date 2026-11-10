from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_organization, require_admin
from app.core.exceptions import ResourceNotFoundException
from app.db.models import ClientWorkspace, Organization, User
from app.db.session import get_db
from app.schemas.organization import ClientWorkspaceCreate, ClientWorkspaceResponse
from app.services.billing_service import BillingService

router = APIRouter(prefix="/clients", tags=["Clients Management"])


@router.get("", response_model=List[ClientWorkspaceResponse])
def list_clients(
    current_user: User = Depends(require_admin),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    return (
        db.query(ClientWorkspace)
        .filter(ClientWorkspace.organization_id == org.id)
        .order_by(ClientWorkspace.created_at.desc())
        .all()
    )


@router.post("", response_model=ClientWorkspaceResponse)
def create_client(
    req: ClientWorkspaceCreate,
    current_user: User = Depends(require_admin),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    # Check plan limit for multi-client feature
    BillingService.check_can_add_client(db, org)

    client = ClientWorkspace(
        organization_id=org.id,
        name=req.name,
        industry=req.industry or "Marketing",
        logo_url=req.logo_url or "",
        notes=req.notes or "",
        is_active=True,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}")
def delete_client(
    client_id: int,
    current_user: User = Depends(require_admin),
    org: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db),
):
    client = (
        db.query(ClientWorkspace)
        .filter(
            ClientWorkspace.id == client_id,
            ClientWorkspace.organization_id == org.id,
        )
        .first()
    )
    if not client:
        raise ResourceNotFoundException("Client Workspace")

    db.delete(client)
    db.commit()
    return {"message": "Client workspace deleted successfully."}

