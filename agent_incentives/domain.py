"""Pure monthly incentive arithmetic and period rules."""
from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import math

VERSION = "payment-entry-v1"

def amount(value):
    result = Decimal(str(value or 0))
    if not result.is_finite():
        raise ValueError("Amounts must be finite")
    return result

def money(value):
    return amount(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def month_period(value):
    day = date.fromisoformat(str(value)[:10])
    return day.replace(day=1), day.replace(day=monthrange(day.year, day.month)[1])

def calculate(received, threshold, percentage, rounding="No Rounding"):
    received, threshold, percentage = map(amount, (received, threshold, percentage))
    if received < 0 or threshold < 0 or not 0 <= percentage <= 100:
        raise ValueError("Invalid collection, threshold or incentive percentage")
    eligible = max(received - threshold, Decimal(0))
    payout = money(eligible * percentage / 100)
    step = {"No Rounding": Decimal(".01"), "Nearest Rupee": Decimal(1), "Nearest 10": Decimal(10)}.get(rounding)
    if step is None:
        raise ValueError("Unsupported rounding rule")
    payout = (payout / step).quantize(Decimal(1), rounding=ROUND_HALF_UP) * step
    return dict(eligible_amount=money(eligible), payout_amount=money(payout))

def threshold(plan):
    if plan.get("threshold_mode") == "Salary Multiple":
        return money(amount(plan.get("salary_amount")) * amount(plan.get("threshold_multiplier")))
    return money(plan.get("threshold_amount"))
