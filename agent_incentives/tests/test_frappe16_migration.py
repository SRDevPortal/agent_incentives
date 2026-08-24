import frappe
from frappe.tests import IntegrationTestCase

from agent_incentives.install import setup_all
from agent_incentives.services.attribution import validate_invoice_attribution_support


class TestAgentIncentivesFrappe16Migration(IntegrationTestCase):
    def test_setup_is_idempotent(self):
        setup_all()
        setup_all()

        for fieldname in (
            "incentive_agent",
            "incentive_agent_name",
            "incentive_locked",
        ):
            self.assertTrue(
                frappe.db.exists("Custom Field", f"Sales Invoice-{fieldname}")
            )

    def test_required_attribution_fields_are_available(self):
        setup_all()

        support = validate_invoice_attribution_support()

        self.assertTrue(support["ok"])
        self.assertEqual(support["missing_fields"], [])

    def test_custom_field_metadata(self):
        setup_all()

        meta = frappe.get_meta("Sales Invoice")
        incentive_agent = meta.get_field("incentive_agent")
        incentive_agent_name = meta.get_field("incentive_agent_name")
        incentive_locked = meta.get_field("incentive_locked")

        self.assertEqual(incentive_agent.fieldtype, "Link")
        self.assertEqual(incentive_agent.options, "User")
        self.assertEqual(incentive_agent_name.read_only, 1)
        self.assertEqual(incentive_locked.fieldtype, "Check")
