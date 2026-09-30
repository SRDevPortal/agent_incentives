"""Serialize enrollment across the two independent reward applications."""
import frappe

TABLES = {
    "incentives": ("Agent Incentive Enrollment", "Agent Incentive Settings"),
    "wfh": ("WFH Enrollment", "WFH Commission Settings"),
}

def lock_participation():
    # Same existing row on every site; current reads below avoid snapshot races.
    frappe.db.sql("select name from tabDocType where name='User' for update")

def active_in(program, user):
    child, parent = TABLES[program]
    if not frappe.db.exists("DocType", child):
        return False
    return bool(frappe.db.sql(
        "select name from `tab" + child + "` where user=%s and active=1 "
        "and parent=%s and parenttype=%s for update",
        (user, parent, parent)))

def assert_exclusive(program, users):
    lock_participation()
    other = "wfh" if program == "incentives" else "incentives"
    for user in sorted(set(users)):
        if active_in(other, user):
            label = "WFH Commission" if other == "wfh" else "Agent Incentives"
            frappe.throw(f"{user} is already actively enrolled in {label}. "
                         "Deactivate that enrollment before enrolling here.")

def validate_enrollment(doc, method=None):
    program = "wfh" if doc.doctype == "WFH Commission Settings" else "incentives"
    assert_exclusive(program, [r.user for r in doc.get("enrollments") or [] if r.active])
