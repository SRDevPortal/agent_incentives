import frappe

def protect_attribution(doc, method=None):
    if doc.is_new():
        return
    previous=doc.get_doc_before_save()
    if not previous:
        return
    changed=any(previous.get(f)!=doc.get(f) for f in ("incentive_agent","incentive_agent_name"))
    if changed and (previous.docstatus==1 or frappe.db.exists("Agent Incentive Source",dict(invoice=doc.name))):
        frappe.throw("Submitted/calculated invoice incentive attribution is immutable; use reviewed correction handling")


def source_changed(doc, method=None):
    """Flag recorded evidence on source changes; never rewrite finalized earnings."""
    import json
    refs=[]
    if doc.doctype=="Payment Entry":
        refs.append(dict(payment_entry=doc.name))
        if doc.get("references"):
            refs.extend(dict(invoice=r.reference_name) for r in doc.references if r.reference_doctype=="Sales Invoice")
    else:
        refs.append(dict(invoice=doc.return_against if doc.get("is_return") and doc.get("return_against") else doc.name))
    ledger_names=set()
    for filters in refs:
        ledger_names.update(frappe.get_all("Agent Incentive Source",filters=filters,pluck="parent"))
    affected={}
    for name in ledger_names:
        ledger=frappe.db.get_value("Agent Incentive Ledger",name,["incentive_run","agent_user"],as_dict=True)
        if ledger:
            affected.setdefault(ledger.incentive_run,set()).add(ledger.agent_user)
    # New/backdated receipts may not have prior evidence yet.
    if doc.doctype=="Payment Entry" and doc.get("posting_date"):
        for row in doc.get("references") or []:
            if row.reference_doctype!="Sales Invoice":
                continue
            owner=frappe.db.get_value("Sales Invoice",row.reference_name,"incentive_agent")
            if not owner:
                continue
            runs=frappe.get_all("Agent Incentive Run",filters=dict(company=doc.company,
                period_start=["<=",doc.posting_date],period_end=[">=",doc.posting_date],
                status=["in",["Calculated","Locked"]]),pluck="name")
            for name in runs:
                if frappe.db.exists("Agent Incentive Ledger",dict(incentive_run=name,agent_user=owner)):
                    affected.setdefault(name,set()).add(owner)
    for run_name,users in affected.items():
        run=frappe.get_doc("Agent Incentive Run",run_name)
        errors=json.loads(run.exceptions_json or "[]")
        for user in users:
            error=dict(user=user,reference=doc.name,error="Recorded source changed; refresh provisional evidence or review a finalized correction")
            if error not in errors:errors.append(error)
        # Non-financial review metadata is independent of frozen amounts.
        run.db_set(dict(exceptions_json=frappe.as_json(errors),exception_count=len(errors)),update_modified=False)
