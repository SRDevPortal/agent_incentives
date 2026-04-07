def calculate_threshold(plan):
    if plan.get("threshold_mode") == "Salary Multiple":
        return float(plan.get("salary_amount") or 0) * float(plan.get("threshold_multiplier") or 0)
    return float(plan.get("threshold_amount") or 0)


def calculate_incentive(net_collected, threshold, incentive_percentage):
    eligible = max(float(net_collected or 0) - float(threshold or 0), 0)
    payout = eligible * (float(incentive_percentage or 0) / 100.0)
    return {
        "eligible_amount": eligible,
        "payout_amount": payout,
    }
