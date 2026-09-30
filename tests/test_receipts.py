import unittest
from unittest.mock import patch, MagicMock
from contextlib import ExitStack
import frappe
from agent_incentives.services.queries import collect

class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.ref=frappe._dict(reference_doctype="Sales Invoice",reference_name="INV-1",allocated_amount=60000)
        self.payment=frappe._dict(name="PE-1",docstatus=1,payment_type="Receive",company="Company",references=[self.ref],party_type="Customer",party="C-1",
            paid_amount=100000,paid_from_account_currency="INR",paid_to_account_currency="INR",
            posting_date="2026-09-01",modified="v1")
        self.invoice=frappe._dict(name="INV-1",incentive_agent="agent",docstatus=1,is_return=0,
            company="Company",customer="C-1",currency="INR",grand_total=100000,modified="v1")
        self.db=MagicMock();self.db.exists.return_value=False
        self.db.sql.side_effect=lambda sql,*args,**kw: [[60000]] if "sum(" in sql else []
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(frappe,"db",new=self.db))
        self.stack.enter_context(patch.object(frappe,"get_meta",return_value=MagicMock()))
        self.stack.enter_context(patch.object(frappe,"get_all",return_value=["PE-1"]))
        self.stack.enter_context(patch.object(frappe,"get_doc",side_effect=lambda dt,name,**kw:self.payment if dt=="Payment Entry" else self.invoice))
    def collect(self):return collect("Company","2026-09-01","2026-09-30",{"agent"})
    def test_only_attributed_allocation_counts(self):
        rows,errors=self.collect()
        self.assertFalse(errors);self.assertEqual(rows[0]["received_amount"],60000)
    def test_overallocation_rejected(self):
        self.payment.paid_amount=50000
        rows,errors=self.collect();self.assertFalse(rows);self.assertTrue(errors)
    def test_duplicate_pair_rejected(self):
        self.payment.references.append(self.ref.copy())
        rows,errors=self.collect();self.assertFalse(rows);self.assertTrue(errors)
    def test_customer_mismatch(self):
        self.payment.party="wrong"
        self.assertTrue(self.collect()[1])
    def test_currency_mismatch(self):
        self.payment.paid_to_account_currency="USD"
        self.assertTrue(self.collect()[1])
    def test_return_is_exception_not_subtraction(self):
        self.db.exists.return_value=True
        rows,errors=self.collect();self.assertFalse(rows);self.assertIn("no automatic",errors[0]["error"])
    def test_missing_owner_is_global_exception(self):
        self.invoice.incentive_agent=None
        rows,errors=self.collect();self.assertFalse(rows);self.assertIsNone(errors[0]["user"])
    def test_other_agent_not_counted(self):
        self.invoice.incentive_agent="other"
        self.assertEqual(self.collect(),([],[]))
    def test_replaced_child_keeps_identity(self):
        before=self.collect()[0][0]["source_key"]
        self.ref.name="replacement"
        self.assertEqual(self.collect()[0][0]["source_key"],before)
    def test_negative_allocation(self):
        self.ref.allocated_amount=-1
        self.assertTrue(self.collect()[1])
    def test_invoice_cap_across_receipts(self):
        self.db.sql.side_effect=lambda sql,*args,**kw: [[200000]] if "sum(" in sql else []
        self.assertTrue(self.collect()[1])
    def test_refund_requires_review(self):
        self.db.sql.side_effect=lambda sql,*args,**kw: [[60000]] if "sum(" in sql else [["REFUND"]]
        self.assertTrue(self.collect()[1])

    def test_draft_receipt_rejected_on_revalidation(self):
        self.payment.docstatus=0
        self.assertTrue(self.collect()[1])
    def test_outgoing_receipt_rejected_on_revalidation(self):
        self.payment.payment_type="Pay"
        self.assertTrue(self.collect()[1])
    def test_missing_posting_date_rejected(self):
        self.payment.posting_date=None
        self.assertTrue(self.collect()[1])
