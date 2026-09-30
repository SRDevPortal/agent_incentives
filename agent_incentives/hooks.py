app_name = "agent_incentives"
app_title = "Agent Incentives"
app_publisher = "SRIAAS"
app_description = "Monthly Payment Entry based agent incentives"
app_email = "webdevelopersriaas@gmail.com"
app_license = "MIT"
required_apps = ["erpnext"]
fixtures = []
after_install = "agent_incentives.setup.install"
after_migrate = "agent_incentives.setup.install"
page_js = {"vobiz-agent-analytics": "public/js/agent_incentive_cards.js"}
doctype_js = {"User": "public/js/user.js"}
doc_events = {
    "Sales Invoice": {
        "validate": "agent_incentives.events.protect_attribution",
        "on_submit": "agent_incentives.events.source_changed",
        "on_cancel": "agent_incentives.events.source_changed",
        "on_update_after_submit": "agent_incentives.events.source_changed"
    },
    "Payment Entry": {
        "on_submit": "agent_incentives.events.source_changed",
        "on_cancel": "agent_incentives.events.source_changed",
        "on_update_after_submit": "agent_incentives.events.source_changed"
    },
}
