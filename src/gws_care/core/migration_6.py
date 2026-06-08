"""DB migration v0.25.0 — Add gws_care_uploaded_document table.

Stores documents uploaded directly by staff (not tied to an Exam).
"""

import uuid

from gws_core import BrickMigration, SqlMigrator, Version, brick_migration

from gws_care.core.care_db_manager import CareDbManager


@brick_migration(
    "0.25.0",
    short_description="Add gws_care_uploaded_document table for standalone document uploads",
    db_manager=CareDbManager.get_instance(),
)
class Migration0250(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        db = CareDbManager.get_instance().db
        db.execute_sql("""
            CREATE TABLE IF NOT EXISTS gws_care_uploaded_document (
                id VARCHAR(36) NOT NULL PRIMARY KEY,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_modified_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_by_id VARCHAR(36) NULL,
                last_modified_by_id VARCHAR(36) NULL,
                patient_id VARCHAR(36) NULL,
                doc_type VARCHAR(80) NULL,
                doc_date DATE NULL,
                description TEXT NULL,
                notes TEXT NULL,
                original_name VARCHAR(500) NOT NULL DEFAULT '',
                resource_id VARCHAR(36) NULL,
                detected_type VARCHAR(80) NULL,
                detected_date VARCHAR(20) NULL,
                detected_patient_name TEXT NULL,
                CONSTRAINT fk_ud_patient FOREIGN KEY (patient_id)
                    REFERENCES gws_care_patient (id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
