# app/crud/application.py

from sqlalchemy.orm import Session
from app.models.application import Application
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.services.embedding_service import embedding_service
from typing import List, Optional
from uuid import UUID
import logging


logger = logging.getLogger(__name__)


def get_application(db: Session, application_id: UUID) -> Optional[Application]:
    return db.query(Application).filter(Application.id == application_id).first()


def get_applications(db: Session, user_id: UUID) -> List[Application]:
    return db.query(Application).filter(Application.user_id == user_id).all()


def create_application(
    db: Session, user_id: UUID, application_in: ApplicationCreate
) -> Application:
    # Generate embedding if not provided
    if not application_in.job_embedding:
        try:
            job_embedding = embedding_service.generate_embedding(
                application_in.job_description_text
            )
            application_data = application_in.model_dump()
            application_data["job_embedding"] = job_embedding
        except Exception as e:
            logger.error(f"Failed to generate job embedding: {str(e)}")
            application_data = application_in.model_dump()
    else:
        application_data = application_in.model_dump()

    db_application = Application(**application_data, user_id=user_id)
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

    update_data = application_in.model_dump(exclude_unset=True)

    # Regenerate embedding if job description changed
    if "job_description_text" in update_data and not update_data.get("job_embedding"):
        try:
            job_embedding = embedding_service.generate_job_embedding(
                update_data["job_description_text"]
            )
            update_data["job_embedding"] = job_embedding
        except Exception as e:
            logger.error(f"Failed to generate job embedding: {str(e)}")

    for field, value in update_data.items():
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
