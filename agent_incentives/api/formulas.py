from agent_incentives.domain import calculate, threshold

def calculate_threshold(plan):
    return float(threshold(plan))

def calculate_incentive(payment_entry_received, threshold, incentive_percentage):
    return {key: float(value) for key, value in calculate(payment_entry_received, threshold, incentive_percentage).items()}
