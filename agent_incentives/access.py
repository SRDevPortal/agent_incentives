import frappe
from agent_incentives.participation import assert_exclusive, lock_participation

INTERNAL = object()

def finance():
    frappe.only_for("System Manager")

def settings():
    return frappe.get_single("Agent Incentive Settings")

def eligible(user, company):
    assert_exclusive("incentives", [user])
    s = settings()
    if not s.enabled or s.company != company:
        frappe.throw("Enable Agent Incentive Settings for the selected company")
    rows = [r for r in s.enrollments if r.user == user and r.active]
    if len(rows) != 1 or not frappe.db.get_value("User", user, "enabled"):
        frappe.throw("An enabled User with one active incentive enrollment is required: " + user)
    return rows[0]

def internal(doc):
    if doc.flags.incentive_write is not INTERNAL:
        frappe.throw("Use the Incentive Workbench actions; financial snapshots are read-only")

def stamp(doc):
    doc.flags.incentive_write = INTERNAL
    return doc
