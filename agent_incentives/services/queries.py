import frappe

from agent_incentives.agent_incentives.services.attribution import resolve_incentive_owner_from_invoice


def get_collection_rows(company, period_start, period_end):
    payment_entries = frappe.get_all(
        "Payment Entry",
        filters={
            "docstatus": 1,
            "payment_type": "Receive",
            "company": company,
            "posting_date": ["between", [period_start, period_end]],
        },
        fields=["name", "posting_date"],
    )
    rows = []
    for pe in payment_entries:
        refs = frappe.get_all(
            "Payment Entry Reference",
            filters={
                "parent": pe.name,
                "parenttype": "Payment Entry",
                "reference_doctype": "Sales Invoice",
            },
            fields=["reference_name", "allocated_amount"],
        )
        for ref in refs:
            if not ref.allocated_amount:
                continue
            owner = resolve_incentive_owner_from_invoice(ref.reference_name)
            rows.append({
                "payment_entry": pe.name,
                "posting_date": pe.posting_date,
                "invoice": ref.reference_name,
                "allocated_amount": float(ref.allocated_amount or 0),
                "agent_user": owner["agent_user"],
                "agent_name": owner["agent_name"],
            })
    return rows


def get_credit_note_rows(company, period_start, period_end):
    sales_invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "company": company,
            "is_return": 1,
            "posting_date": ["between", [period_start, period_end]],
        },
        fields=["name", "posting_date", "return_against", "grand_total", "rounded_total"],
    )
    rows = []
    for inv in sales_invoices:
        source_invoice = inv.return_against or inv.name
        owner = resolve_incentive_owner_from_invoice(source_invoice)
        deduction = abs(float(inv.rounded_total or inv.grand_total or 0))
        rows.append({
            "credit_note": inv.name,
            "posting_date": inv.posting_date,
            "source_invoice": source_invoice,
            "deduction_amount": deduction,
            "agent_user": owner["agent_user"],
            "agent_name": owner["agent_name"],
        })
    return rows
