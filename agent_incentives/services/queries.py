"""Invoice-attributed allocations confirmed by submitted Receive Payment Entries."""
import hashlib
import json
import frappe
from agent_incentives.domain import money

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()

def collect(company, start, end, users):
    rows, errors = [], []
    if not users:
        return rows, errors
    meta = frappe.get_meta("Sales Invoice")
    if not all(meta.has_field(f) for f in ("incentive_agent", "incentive_agent_name")):
        return [], [dict(user=None, reference="Sales Invoice", error="Required invoice incentive attribution fields are missing")]
    payments = frappe.get_all("Payment Entry", filters=dict(company=company, docstatus=1, payment_type="Receive",
        posting_date=["between", [start, end]]), pluck="name", order_by="name")
    for name in payments:
        pe = frappe.get_doc("Payment Entry", name, for_update=True)
        refs = [r for r in pe.references if r.reference_doctype == "Sales Invoice" and r.allocated_amount]
        for ref in refs:
            owner = None
            try:
                inv = frappe.get_doc("Sales Invoice", ref.reference_name, for_update=True)
                owner = inv.get("incentive_agent")
                if owner and owner not in users:
                    continue
                if not owner:
                    raise ValueError("Invoice incentive owner is missing")
                if pe.docstatus != 1 or pe.payment_type != "Receive" or pe.company != company or not pe.posting_date:
                    raise ValueError("Receipt must remain a submitted company Receive Payment Entry")
                if inv.docstatus != 1 or inv.is_return or inv.company != company:
                    raise ValueError("A submitted non-return company invoice is required")
                if pe.party_type != "Customer" or pe.party != inv.customer:
                    raise ValueError("Payment Entry customer differs from invoice")
                if inv.currency != "INR" or pe.paid_from_account_currency != "INR" or pe.paid_to_account_currency != "INR":
                    raise ValueError("Only INR invoices and receipts are supported")
                receipt = money(pe.paid_amount)
                allocated = money(ref.allocated_amount)
                all_amounts = [money(r.allocated_amount) for r in pe.references if r.allocated_amount]
                if receipt <= 0 or allocated <= 0 or any(a < 0 for a in all_amounts) or sum(all_amounts) > receipt:
                    raise ValueError("Allocations must be positive and within confirmed Payment Entry amount")
                same = [r for r in refs if r.reference_name == inv.name]
                if len(same) != 1:
                    raise ValueError("Duplicate Payment Entry/invoice allocations require review")
                if allocated > money(inv.grand_total):
                    raise ValueError("Allocation exceeds invoice total")
                # Bound allocations across submitted receipts as well as within this receipt.
                total = frappe.db.sql("""select coalesce(sum(r.allocated_amount),0)
                    from `tabPayment Entry Reference` r join `tabPayment Entry` p on p.name=r.parent
                    where r.parenttype='Payment Entry' and r.reference_doctype='Sales Invoice'
                    and r.reference_name=%s and p.docstatus=1 and p.payment_type='Receive'""", inv.name)[0][0]
                if money(total) > money(inv.grand_total):
                    raise ValueError("Submitted receipt allocations exceed invoice total")
                if frappe.db.exists("Sales Invoice", dict(return_against=inv.name, is_return=1, docstatus=1)):
                    raise ValueError("Returned/credited invoice requires reviewed correction; no automatic credit-note deduction")
                refund = frappe.db.sql("""select p.name from `tabPayment Entry` p
                    join `tabPayment Entry Reference` r on r.parent=p.name
                    where p.docstatus=1 and p.payment_type='Pay' and r.reference_doctype='Sales Invoice'
                    and r.reference_name=%s limit 1""", inv.name)
                if refund:
                    raise ValueError("Refunded invoice requires finance review")
                row = dict(source_key=digest([pe.name, inv.name]), payment_entry=pe.name,
                    invoice=inv.name, posting_date=str(pe.posting_date), received_amount=float(allocated), agent_user=owner)
                row["fingerprint"] = digest([row, str(pe.modified), str(inv.modified), str(receipt), str(total)])
                rows.append(row)
            except (ValueError, frappe.ValidationError, frappe.DoesNotExistError) as exc:
                errors.append(dict(user=owner, reference=name + " / " + ref.reference_name, error=str(exc)))
    return rows, errors

def get_collection_rows(company, period_start, period_end):
    from agent_incentives.access import settings
    users = {r.user for r in settings().enrollments if r.active}
    rows, errors = collect(company, period_start, period_end, users)
    if errors:
        frappe.throw("Receipt exceptions require review")
    return [dict(r, agent_name=frappe.db.get_value("User", r["agent_user"], "full_name"),
                 allocated_amount=r["received_amount"]) for r in rows]
