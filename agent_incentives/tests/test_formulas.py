from frappe.tests import UnitTestCase

from agent_incentives.api.formulas import calculate_incentive, calculate_threshold


class TestIncentiveFormulas(UnitTestCase):
    def test_salary_multiple_threshold(self):
        threshold = calculate_threshold(
            {
                "threshold_mode": "Salary Multiple",
                "salary_amount": 25_000,
                "threshold_multiplier": 1.5,
            }
        )

        self.assertEqual(threshold, 37_500)

    def test_fixed_threshold(self):
        threshold = calculate_threshold(
            {
                "threshold_mode": "Fixed Amount",
                "threshold_amount": 40_000,
            }
        )

        self.assertEqual(threshold, 40_000)

    def test_incentive_is_zero_below_threshold(self):
        result = calculate_incentive(20_000, 25_000, 10)

        self.assertEqual(result["eligible_amount"], 0)
        self.assertEqual(result["payout_amount"], 0)

    def test_incentive_uses_only_eligible_amount(self):
        result = calculate_incentive(50_000, 30_000, 7.5)

        self.assertEqual(result["eligible_amount"], 20_000)
        self.assertEqual(result["payout_amount"], 1_500)
