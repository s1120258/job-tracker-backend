from sqlalchemy.orm import Session
from app.models.application import Application
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from typing import List, Optional
from uuid import UUID


def get_application(db: Session, application_id: UUID) -> Optional[Application]:
    return db.query(Application).filter(Application.id == application_id).first()


def get_applications(db: Session, user_id: UUID) -> List[Application]:
    return db.query(Application).filter(Application.user_id == user_id).all()


def create_application(
    db: Session, user_id: UUID, application_in: ApplicationCreate
) -> Application:
    db_application = Application(**application_in.dict(), user_id=user_id)
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application


def update_application(
    db: Session, application_id: UUID, application_in: ApplicationUpdate
) -> Optional[Application]:
    db_application = get_application(db, application_id)
    if not db_application:
        return None
    for field, value in application_in.dict(exclude_unset=True).items():
        setattr(db_application, field, value)
    db.commit()
    db.refresh(db_application)
    return db_application


def delete_application(db: Session, application_id: UUID) -> bool:
    db_application = get_application(db, application_id)
    if not db_application:
        return False
    db.delete(db_application)
    db.commit()
    return True
