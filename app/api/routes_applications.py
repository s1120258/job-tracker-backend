# app/api/routes_applications.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.db.session import get_db
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationRead,
)
from app.crud import application as crud_application
from app.api.routes_auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/applications", response_model=List[ApplicationRead])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_application.get_applications(db, user_id=current_user.id)


@router.post(
    "/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED
)
def create_application(
    application_in: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_application.create_application(
        db, user_id=current_user.id, application_in=application_in
    )


@router.get("/applications/{application_id}", response_model=ApplicationRead)
def get_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = crud_application.get_application(db, application_id)
    if not app or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.put("/applications/{application_id}", response_model=ApplicationRead)
def update_application(
    application_id: UUID,
    application_in: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = crud_application.get_application(db, application_id)
    if not app or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")
    return crud_application.update_application(db, application_id, application_in)


@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    app = crud_application.get_application(db, application_id)
    if not app or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")
    crud_application.delete_application(db, application_id)
    return None
