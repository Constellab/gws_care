"""State for the medical certificates list page."""

import reflex as rx
from pydantic import BaseModel
from gws_reflex_main import ReflexMainState


class CertificateRowDTO(BaseModel):
    id: str = ""
    patient_id: str = ""
    patient_name: str = ""
    patient_number: str = ""
    issue_date: str = ""
    is_fit_for_work: bool = True
    conclusion: str = ""
    restrictions: str = ""
    issued_by_name: str = ""
    exam_id: str = ""


class CertificatesState(ReflexMainState):
    rows: list[CertificateRowDTO] = []
    is_loading: bool = False
    error_message: str = ""
    search_query: str = ""
    fit_filter: str = "ALL"   # "ALL" | "FIT" | "NOT_FIT"

    @rx.var
    def filtered_rows(self) -> list[CertificateRowDTO]:
        rows = self.rows
        if self.fit_filter == "FIT":
            rows = [r for r in rows if r.is_fit_for_work]
        elif self.fit_filter == "NOT_FIT":
            rows = [r for r in rows if not r.is_fit_for_work]
        q = self.search_query.strip().lower()
        if not q:
            return rows
        return [
            r for r in rows
            if q in r.patient_name.lower()
            or q in r.patient_number.lower()
            or q in r.issued_by_name.lower()
            or q in r.conclusion.lower()
        ]

    @rx.event
    def set_search(self, value: str):
        self.search_query = value

    @rx.event
    def set_fit_filter(self, value: str):
        self.fit_filter = value

    @rx.event
    async def on_load(self):
        self.is_loading = True
        self.error_message = ""
        try:
            with await self.authenticate_user():
                from gws_care.certificate.medical_certificate import MedicalCertificate
                from gws_care.patient.patient import Patient
                from gws_care.user.user import User

                certs = list(
                    MedicalCertificate.select(MedicalCertificate, Patient)
                    .join(Patient)
                    .order_by(MedicalCertificate.issue_date.desc())
                    .limit(200)
                )
                # Preload issuing users in one query (avoids N+1)
                user_ids = {cert.issued_by_id for cert in certs if cert.issued_by_id}
                user_names: dict[str, str] = {}
                if user_ids:
                    from gws_care.user.user import User
                    for u in User.select(User.id, User.first_name, User.last_name, User.email).where(User.id.in_(user_ids)):
                        user_names[str(u.id)] = f"{u.first_name} {u.last_name}".strip() or u.email
                rows: list[CertificateRowDTO] = []
                for cert in certs:
                    issued_by_name = user_names.get(str(cert.issued_by_id), "") if cert.issued_by_id else ""
                    rows.append(CertificateRowDTO(
                        id=str(cert.id),
                        patient_id=str(cert.patient_id),
                        patient_name=cert.patient.get_full_name(),
                        patient_number=cert.patient.patient_number or "",
                        issue_date=cert.issue_date.isoformat() if cert.issue_date else "",
                        is_fit_for_work=bool(cert.is_fit_for_work),
                        conclusion=cert.conclusion or "",
                        restrictions=cert.restrictions or "",
                        issued_by_name=issued_by_name,
                        exam_id=str(cert.exam_id) if cert.exam_id else "",
                    ))
                self.rows = rows
        except Exception as exc:
            self.error_message = str(exc)
            print(f"[certificates] Erreur chargement: {exc}")
        finally:
            self.is_loading = False
