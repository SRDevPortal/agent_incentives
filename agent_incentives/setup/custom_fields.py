import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


SALES_INVOICE_CUSTOM_FIELDS = {
    "Sales Invoice": [
        {
            "fieldname": "incentive_agent",
            "label": "Incentive Agent",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "customer_name",
            "in_standard_filter": 1,
        },
        {
            "fieldname": "incentive_agent_name",
            "label": "Incentive Agent Name",
            "fieldtype": "Data",
            "insert_after": "incentive_agent",
            "fetch_from": "incentive_agent.full_name",
            "fetch_if_empty": 1,
            "read_only": 1,
        },
        {
            "fieldname": "incentive_locked",
            "label": "Incentive Attribution Locked",
            "fieldtype": "Check",
            "insert_after": "incentive_agent_name",
            "default": "0",
            "read_only": 1,
        },
    ]
}


def ensure_custom_fields():
    """Create fields owned by Agent Incentives without requiring optional apps."""
    if not frappe.db.exists("DocType", "Sales Invoice"):
        return

    create_custom_fields(SALES_INVOICE_CUSTOM_FIELDS, update=True)
    frappe.clear_cache(doctype="Sales Invoice")
