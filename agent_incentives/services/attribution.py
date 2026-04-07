import frappe


REQUIRED_INVOICE_FIELDS = [
    "incentive_agent",
    "incentive_agent_name",
]

OPTIONAL_INVOICE_FIELDS = [
    "source_encounter",
    "incentive_locked",
]


def get_sales_invoice_fieldnames():
    if not frappe.db.exists("DocType", "Sales Invoice"):
        return set()
    return {f.fieldname for f in frappe.get_meta("Sales Invoice").fields}


def validate_invoice_attribution_support():
    fields = get_sales_invoice_fieldnames()
    missing = [f for f in REQUIRED_INVOICE_FIELDS if f not in fields]
    return {
        "ok": not missing,
        "missing_fields": missing,
        "available_fields": sorted(fields),
    }


def resolve_incentive_owner_from_invoice(invoice_name):
    support = validate_invoice_attribution_support()
    if not support["ok"]:
        frappe.throw(
            "Sales Invoice is missing required attribution fields: " + ", ".join(support["missing_fields"])
        )

    invoice = frappe.db.get_value(
        "Sales Invoice",
        invoice_name,
        ["incentive_agent", "incentive_agent_name"],
        as_dict=True,
    )
    if not invoice:
        frappe.throw(f"Sales Invoice {invoice_name} not found.")
    if not invoice.incentive_agent:
        frappe.throw(f"Sales Invoice {invoice_name} has no incentive attribution owner.")

    return {
        "agent_user": invoice.incentive_agent,
        "agent_name": invoice.incentive_agent_name or invoice.incentive_agent,
        "source": "sales_invoice",
    }
