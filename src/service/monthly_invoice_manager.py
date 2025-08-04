import logfire

from data import monthly_invoice
from data.models.invoice_models import MonthlyInvoice
from service.database_manager import get_db_connection

logfire.configure()


def update_invoice_on_db(month_invoice: MonthlyInvoice) -> None:
    logfire.info(
        f"SERVICE-OP: Updating monthly invoice {month_invoice.id} for patient {month_invoice.patient_id}"
    )
    connection = get_db_connection()
    monthly_invoice.update(connection, month_invoice)
    logfire.info(f"SERVICE-OP: Successfully updated monthly invoice {month_invoice.id}")


def get_monthly_invoices(chosen_month: int, chosen_year: int) -> list[MonthlyInvoice]:
    logfire.info(
        f"SERVICE-OP: Fetching monthly invoices for {chosen_month}/{chosen_year}"
    )
    connection = get_db_connection()
    invoices = monthly_invoice.get_all_in_period(connection, chosen_month, chosen_year)
    logfire.info(
        f"SERVICE-OP: Retrieved {len(invoices)} invoices for {chosen_month}/{chosen_year}"
    )
    return invoices
