from datetime import date
from dateutil.relativedelta import relativedelta

RETENTION_YEARS = {"UM": 5, "TER": 10, "RHS": 20}

def compute_retention_until(code: str | None, start_date: date):
    years = RETENTION_YEARS.get((code or "").upper(), 5)
    return start_date + relativedelta(years=years)
