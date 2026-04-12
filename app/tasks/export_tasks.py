"""LoanAxis CRM — Export Celery Tasks"""
from app.extensions import celery


@celery.task(name="tasks.async_generate_report")
def async_generate_report(report_type, filters=None):
    """Generate large reports asynchronously. Notifies user when ready."""
    from app.models.lead import Lead
    from app.utils.export_utils import leads_to_xlsx
    import os, tempfile

    if report_type == "leads":
        leads = Lead.query.filter_by(is_deleted=False).all()
        output = leads_to_xlsx(leads)
        # Save to temp file
        filepath = os.path.join("uploads", "exports", f"leads_report_{report_type}.xlsx")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            f.write(output.getvalue())
        return {"status": "complete", "filepath": filepath}
    return {"status": "unknown_type"}
