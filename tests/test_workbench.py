import unittest
from decimal import Decimal
from unittest.mock import patch, MagicMock
import frappe
from agent_incentives.domain import calculate, threshold, month_period
from agent_incentives import participation
from wfh_commission import participation as wfh_participation

class FormulaTests(unittest.TestCase):
    def test_received_threshold_example(self):
        self.assertEqual(calculate(200000,50000,5)["payout_amount"],Decimal("7500.00"))
    def test_multiple_receipts_apply_threshold_once(self):
        self.assertEqual(calculate(60000+40000,50000,5)["payout_amount"],Decimal("2500"))
    def test_below_threshold(self):
        self.assertEqual(calculate(40000,50000,5)["payout_amount"],0)
    def test_salary_threshold(self):
        self.assertEqual(threshold(dict(threshold_mode="Salary Multiple",salary_amount=25000,threshold_multiplier=2)),50000)
    def test_rounding(self):
        self.assertEqual(calculate(12345,0,5,"Nearest 10")["payout_amount"],620)
    def test_nonfinite_and_negative_rejected(self):
        for v in ("NaN","Infinity",-1):
            with self.assertRaises(ValueError):calculate(v,0,5)
    def test_invalid_rate(self):
        with self.assertRaises(ValueError):calculate(100,0,101)
    def test_calendar_month(self):
        self.assertEqual(str(month_period("2024-02-10")[1]),"2024-02-29")

class ParticipationTests(unittest.TestCase):
    def test_both_directions_reject_other_active(self):
        for module,program in ((participation,"incentives"),(wfh_participation,"wfh")):
            with patch.object(module,"lock_participation") as lock,patch.object(module,"active_in",return_value=True),patch.object(frappe,"throw",side_effect=ValueError):
                with self.assertRaises(ValueError):module.assert_exclusive(program,["agent"])
                lock.assert_called_once()
    def test_inactive_history_allows_switch(self):
        for module,program in ((participation,"incentives"),(wfh_participation,"wfh")):
            with patch.object(module,"lock_participation"),patch.object(module,"active_in",return_value=False):
                module.assert_exclusive(program,["agent"])
    def test_optional_other_app(self):
        with patch.object(frappe,"db",new=MagicMock()) as db:
            db.exists.return_value=False
            self.assertFalse(participation.active_in("wfh","agent"))
            db.sql.assert_not_called()
    def test_current_read_and_parent_scope(self):
        with patch.object(frappe,"db",new=MagicMock()) as db:
            db.exists.return_value=True;db.sql.return_value=[["enrollment"]]
            self.assertTrue(participation.active_in("wfh","agent"))
            sql,args=db.sql.call_args.args
            self.assertIn("for update",sql)
            self.assertEqual(args,("agent","WFH Commission Settings","WFH Commission Settings"))
    def test_settings_only_checks_active_rows(self):
        doc=frappe._dict(doctype="WFH Commission Settings",enrollments=[
            frappe._dict(user="active",active=1),frappe._dict(user="historical",active=0)])
        with patch.object(participation,"assert_exclusive") as check:
            participation.validate_enrollment(doc)
            check.assert_called_once_with("wfh",["active"])

class SecurityTests(unittest.TestCase):
    def test_self_endpoint_has_no_user_selector(self):
        import inspect
        from agent_incentives.agent_dashboard import my_incentive_cards
        self.assertEqual(list(inspect.signature(my_incentive_cards).parameters),[])
    def test_forged_internal_flag_fails(self):
        from agent_incentives.access import internal
        doc=frappe._dict(flags=frappe._dict(incentive_write=True))
        with patch.object(frappe,"throw",side_effect=ValueError):
            with self.assertRaises(ValueError):internal(doc)

if __name__=="__main__":unittest.main()
