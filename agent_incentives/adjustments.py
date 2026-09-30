import frappe
from agent_incentives.domain import money

def amounts(company, user=None):
    filters=dict(company=company)
    if user:filters["agent_user"]=user
    rows=frappe.get_all("Agent Incentive Adjustment",filters=filters,fields=["agent_user","amount"])
    totals={}
    for row in rows:totals[row.agent_user]=totals.get(row.agent_user,money(0))+money(row.amount)
    return totals

def for_ledger(ledger):
    return sum((money(r.amount) for r in frappe.get_all("Agent Incentive Adjustment",
        filters=dict(ledger=ledger),fields=["amount"])),money(0))
