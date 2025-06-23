# 🗂️ Data Model (ERD)

This document describes the core data model for the Job Tracker backend. It includes an Entity Relationship Diagram (ERD) and a summary of each main table/entity.

---

## Entity Relationship Diagram

![Entity Relationship Diagram](./ERD.png)

---

## Table Summaries

### users

- **id**: UUID, primary key
- **email**: String, unique
- **hashed_password**: String
- **created_at**: Timestamp
- **Relations**: One user has one resume and many applications

### resumes

- **id**: UUID, primary key
- **user_id**: UUID, foreign key to users
- **file_path**: String
- **file_name**: String
- **upload_date**: Timestamp
- **extracted_text**: Text
- **llm_feedback**: Text
- **embedding**: Vector(1536)
- **Relations**: One resume per user (enforced in logic)

### applications

- **id**: UUID, primary key
- **user_id**: UUID, foreign key to users
- **company_name**: String
- **position_title**: String
- **job_description_text**: Text
- **job_embedding**: Vector(1536)
- **application_status**: Enum (applied, interviewing, rejected, offer, accepted)
- **applied_date**: Date
- **interview_date**: Date (optional)
- **offer_date**: Date (optional)
- **notes**: Text
- **created_at**: Timestamp
- **updated_at**: Timestamp
- **Relations**: Many applications per user; one match_score per application

### match_scores

- **id**: UUID, primary key
- **application_id**: UUID, foreign key to applications
- **score**: Float (similarity score)
- **Relations**: One match score per application

---

For more details, see the [README](../README.md) and other docs in this folder.
