from data import monthly_invoice
from data.models.invoice_models import MonthlyInvoice
from service.database_manager import get_db_connection


def update_invoice_on_db(month_invoice: MonthlyInvoice) -> None:
    connection = get_db_connection()
    monthly_invoice.update(connection, month_invoice)


def get_monthly_invoices(chosen_month: int, chosen_year: int) -> list[MonthlyInvoice]:
    connection = get_db_connection()
    return monthly_invoice.get_all_in_period(connection, chosen_month, chosen_year)
