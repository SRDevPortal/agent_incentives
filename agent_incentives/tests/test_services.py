from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from agent_incentives.services.calculation import build_run_rows
from agent_incentives.services.queries import get_collection_rows, get_credit_note_rows


class TestCollectionQueries(UnitTestCase):
    @patch("agent_incentives.services.queries.resolve_incentive_owner_from_invoice")
    @patch("agent_incentives.services.queries.frappe.get_all")
    def test_collection_rows_use_submitted_receipts_and_allocations(self, get_all, resolve_owner):
        get_all.side_effect = [
            [SimpleNamespace(name="PAY-0001", posting_date="2026-08-01")],
            [
                SimpleNamespace(reference_name="SINV-0001", allocated_amount=1_250),
                SimpleNamespace(reference_name="SINV-0002", allocated_amount=0),
            ],
        ]
        resolve_owner.return_value = {
            "agent_user": "agent@example.com",
            "agent_name": "Agent One",
        }

        rows = get_collection_rows("Test Company", "2026-08-01", "2026-08-31")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["allocated_amount"], 1_250)
        self.assertEqual(rows[0]["agent_user"], "agent@example.com")
        resolve_owner.assert_called_once_with("SINV-0001")

    @patch("agent_incentives.services.queries.resolve_incentive_owner_from_invoice")
    @patch("agent_incentives.services.queries.frappe.get_all")
    def test_credit_notes_are_absolute_deductions(self, get_all, resolve_owner):
        get_all.return_value = [
            SimpleNamespace(
                name="SINV-RET-0001",
                posting_date="2026-08-10",
                return_against="SINV-0001",
                grand_total=-500,
                rounded_total=0,
            )
        ]
        resolve_owner.return_value = {
            "agent_user": "agent@example.com",
            "agent_name": "Agent One",
        }

        rows = get_credit_note_rows("Test Company", "2026-08-01", "2026-08-31")

        self.assertEqual(rows[0]["deduction_amount"], 500)
        resolve_owner.assert_called_once_with("SINV-0001")


class TestRunCalculation(UnitTestCase):
    @patch("agent_incentives.services.calculation.get_applicable_plan")
    @patch("agent_incentives.services.calculation.get_credit_note_rows")
    @patch("agent_incentives.services.calculation.get_collection_rows")
    def test_run_rows_apply_credit_notes_and_threshold(
        self,
        get_collections,
        get_credit_notes,
        get_plan,
    ):
        get_collections.return_value = [
            {
                "agent_user": "agent@example.com",
                "agent_name": "Agent One",
                "allocated_amount": 50_000,
            }
        ]
        get_credit_notes.return_value = [
            {
                "agent_user": "agent@example.com",
                "agent_name": "Agent One",
                "deduction_amount": 5_000,
            }
        ]
        get_plan.return_value = frappe._dict(
            name="AIP-0001",
            threshold_mode="Fixed Amount",
            threshold_amount=30_000,
            salary_amount=0,
            threshold_multiplier=0,
            incentive_percentage=10,
        )

        rows = build_run_rows("Test Company", "2026-08-01", "2026-08-31")

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["gross_collected"], 50_000)
        self.assertEqual(rows[0]["credit_note_amount"], 5_000)
        self.assertEqual(rows[0]["net_collected"], 45_000)
        self.assertEqual(rows[0]["eligible_amount"], 15_000)
        self.assertEqual(rows[0]["payout_amount"], 1_500)
