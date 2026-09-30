import unittest
from contextlib import ExitStack
from unittest.mock import patch,MagicMock
import frappe
from agent_incentives import settlements

class SettlementTests(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.doc=frappe._dict(ledger="L",journal_entry="J",journal_row="ROW",amount=400,is_new=lambda:True)
        self.ledger=frappe._dict(name="L",incentive_run="R",agent_user="agent",company="Company",
            calculation_version="payment-entry-v1",final_payout_amount=1000)
        self.run=frappe._dict(status="Locked")
        self.account=frappe._dict(company="Company",account_type="Payable",account_currency="INR",disabled=0,is_group=0)
        self.line=frappe._dict(name="ROW",account="Incentive Payable",party_type="User",party="agent",debit=400,credit=0)
        self.journal=frappe._dict(name="J",company="Company",docstatus=1,posting_date="2026-09-29",check_permission=lambda *a:None,
            accounts=[self.line,frappe._dict(account="Bank",debit=0,credit=400)])
        self.stack.enter_context(patch.object(settlements,"finance"))
        self.stack.enter_context(patch.object(settlements,"lock_participation"))
        self.stack.enter_context(patch.object(settlements,"settings",return_value=frappe._dict(settlement_account="Incentive Payable")))
        self.stack.enter_context(patch.object(frappe,"throw",side_effect=frappe.ValidationError))
        self.db=MagicMock();self.db.exists.return_value=False
        self.db.sql.return_value=[[0]];self.db.get_value.return_value="Bank"
        self.stack.enter_context(patch.object(frappe,"db",new=self.db))
        self.stack.enter_context(patch.object(frappe,"get_doc",side_effect=lambda dt,name:{
            "Agent Incentive Ledger":self.ledger,"Agent Incentive Run":self.run,"Account":self.account,"Journal Entry":self.journal}[dt]))
        self.stack.enter_context(patch("agent_incentives.adjustments.for_ledger",return_value=0))
    def test_partial_payment_verified(self):
        settlements.verify(self.doc)
        self.assertEqual(self.doc.amount,400);self.assertEqual(self.doc.agent_user,"agent")
    def test_duplicate_allocation_rejected(self):
        self.db.sql.return_value=[[400]]
        with self.assertRaises(frappe.ValidationError):settlements.verify(self.doc)
    def test_draft_voucher_rejected(self):
        self.journal.docstatus=0
        with self.assertRaises(frappe.ValidationError):settlements.verify(self.doc)
    def test_other_beneficiary_rejected(self):
        self.line.party="other"
        with self.assertRaises(frappe.ValidationError):settlements.verify(self.doc)
    def test_accrual_not_classified_as_payment(self):
        self.db.get_value.return_value="Payable"
        with self.assertRaises(frappe.ValidationError):settlements.verify(self.doc)
    def test_payment_exceeds_earning(self):
        self.ledger.final_payout_amount=200
        with self.assertRaises(frappe.ValidationError):settlements.verify(self.doc)
    def test_wfh_voucher_rejected(self):
        self.journal.wfh_payout_batch="WFH-BATCH"
        with self.assertRaises(frappe.ValidationError):settlements.verify(self.doc)
    def test_existing_evidence_immutable(self):
        self.doc.is_new=lambda:False
        with self.assertRaises(frappe.ValidationError):settlements.verify(self.doc)
    def test_cancellation_excluded_by_aggregate_query(self):
        self.db.sql.return_value=[]
        settlements.paid_by_user("Company","agent")
        sql,args=self.db.sql.call_args.args
        self.assertIn("j.docstatus=1",sql);self.assertIn("s.agent_user=%s",sql)
        self.assertEqual(args,["Company","agent"])
