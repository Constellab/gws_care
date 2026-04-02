# CLAUDE.md

This file provides guidance to AI assistants (Claude, GitHub Copilot, etc.) when working with code in this repository. All paths are relative to the location of this file.

## Project Overview

`gws_care` is a Constellab brick for managing **occupational health checkups** (bilans médicaux en entreprise) for the company **PS CONSULTING**. It provides:
- A database-backed patient and company management system
- A Reflex web application for operators, doctors, and administrators
- Future integration point with `gws_care_billing` (invoicing, separate brick)

Full specification: `specs/CAHIER DES CHARGES LOGICIEL 2025 V1.pdf`

## Architecture

### Directory Structure
```
src/gws_care/
├── __init__.py                    # Registers models, migration, sync service, and task
├── core/
│   ├── care_db_manager.py         # CareDbManager (LazyAbstractDbManager, brick='gws_care')
│   ├── model_with_user.py         # Base model with created_by / last_modified_by FKs
│   └── migration_0.py             # DB migration v0.1.0: User, Company, Patient tables
├── user/
│   ├── user.py                    # Local User model (mirrors gws_core User)
│   └── care_user_sync_service.py  # Syncs gws_core users into local User table
├── company/
│   ├── company.py                 # Company model (client companies)
│   ├── company_dto.py             # CompanyDTO / SaveCompanyDTO
│   └── company_service.py         # CRUD service: create / update / list / deactivate
├── patient/
│   ├── patient.py                 # Patient model (auto patient_number: PAT-XXXXXXXX)
│   ├── patient_dto.py             # PatientDTO / SavePatientDTO
│   └── patient_service.py         # CRUD service: create / update / search
└── care_app/
    ├── generate_care_app.py        # Constellab Task to generate the Reflex app
    └── _care_app/                  # Reflex app root (prefixed _ to avoid auto-load)
        ├── rxconfig.py
        ├── dev_config.json
        └── care_app/
            ├── care_app.py         # Routes: /, /patient/[id], /companies
            ├── common/
            │   └── page_layout.py  # Sidebar layout (Patients / Companies nav)
            ├── patient_list/       # Patient list page + search filters
            ├── patient_detail/     # Patient detail card (demographics, contact)
            └── company_list/       # Company list page + search
```

### Key Design Decisions
- **User sync**: `CareUserSyncService` mirrors gws_core users into the local `gws_care_user` table so that `ModelWithUser` FK constraints (`created_by`, `last_modified_by`) resolve correctly.
- **Reflex DTOs**: State DTOs (e.g., `PatientRowDTO`) use plain `pydantic.BaseModel`, not `gws_core.ModelDTO` — Reflex requires this for frontend serialization.
- **Authentication in state**: Service calls are wrapped in `with await self.authenticate_user():` to set up gws_core auth context.
- **Billing exclusion**: Invoicing and financial features belong to `gws_care_billing` (separate brick). This brick exposes patient/exam IDs as integration points.

### Dependencies
- `gws_core` (v0.19.3) — ORM, auth, Reflex scaffolding, task system
- `reflex` (v0.8.14.post1) — Web framework for the Care app

## Development Conventions
- Import from `gws_core` using main module (e.g., `from gws_core import Model`) not sub-imports
- Table names prefixed with `gws_care_` (e.g., `gws_care_patient`)
- Patient numbers auto-generated as `PAT-XXXXXXXX` (8 hex chars, uppercase)
- Do not export classes in `__init__.py` unless required

## Development Commands

### Server
```bash
gws server run
gws server run --log-level=DEBUG
```

### Tests
```bash
cd bricks/gws_care && gws server test all
cd bricks/gws_care && gws server test test_table_factor
```

### Run Reflex App (dev mode)
```bash
gws reflex run bricks/gws_care/src/gws_care/care_app/_care_app/dev_config.json
```
