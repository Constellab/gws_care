"""CSV export service for patient exam history."""

import csv
import io


def generate_exam_history_csv(patient_id: str) -> bytes:
    """Generate a UTF-8 CSV of all exams + results for a patient.

    Returns raw bytes ready to pass to rx.download.
    """
    from gws_care.exam.exam import Exam
    from gws_care.exam.exam_result_service import ExamResultService
    from gws_care.account.account import Account
    from peewee import JOIN

    exams = list(
        Exam.select(Exam, Account)
        .join(Account, JOIN.LEFT_OUTER, on=(Exam.billing_account == Account.id))
        .where(Exam.patient == patient_id)
        .order_by(Exam.exam_date.asc())
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Exam Date",
        "Exam Type",
        "Status",
        "Account",
        "Interpretation",
        "Result Data",
        "Notes",
    ])

    for exam in exams:
        result = ExamResultService.get_result_for_exam(str(exam.id))
        result_summary = ""
        if result and result.result_data:
            parts = [f"{k}={v}" for k, v in result.result_data.items() if v]
            result_summary = "; ".join(parts)

        account_name = exam.billing_account.name if exam.billing_account_id else ""

        writer.writerow([
            exam.exam_date.isoformat(),
            exam.exam_type.get_label(),
            exam.status.value,
            account_name,
            exam.interpretation or "",
            result_summary,
            exam.notes or "",
        ])

    return output.getvalue().encode("utf-8-sig")   # utf-8-sig for Excel compat
