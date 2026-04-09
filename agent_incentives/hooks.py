app_name = "agent_incentives"
app_title = "Agent Incentives"
app_publisher = "SRIAAS"
app_description = "Agent incentive engine for encounter-owned payment collections"
app_email = "webdevelopersriaas@gmail.com"
app_license = "MIT"

fixtures = []

scheduler_events = {
    "daily": [
        "agent_incentives.agent_incentives.doctype.agent_incentive_settings.agent_incentive_settings.ensure_single"
    ]
}
