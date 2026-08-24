# Agent Incentives

Internal Frappe app for agent incentive configuration, plan management, and ledger tracking based on encounter-owned collections.

## Current capabilities

- `Agent Incentive Settings` single doctype
- `Agent Incentive Plan` doctype
- `Agent Incentive Run` doctype
- `Agent Incentive Ledger` doctype
- formula helper functions for threshold and payout logic
- setup status API
- smoke-check API

## Requirements

- Frappe 16
- ERPNext 16
- Python 3.14

## Install

```bash
cd /path/to/frappe-bench
bench get-app --branch frappe-16 https://github.com/SRDevPortal/agent_incentives.git
bench --site yoursite install-app agent_incentives
bench --site yoursite migrate
bench --site yoursite clear-cache
```

Installation creates the Sales Invoice fields owned by this app:

- `incentive_agent`
- `incentive_agent_name`
- `incentive_locked`

The optional `source_encounter` field remains owned by its integrating app.

## First-run flow
1. Open `Agent Incentive Settings`
2. Configure threshold defaults and deduction behavio
3. Create one active `Agent Incentive Plan` per sales agent
4. Verify setup using:
   - `/api/method/agent_incentives.api.setup.get_setup_status`
   - `/api/method/agent_incentives.api.setup.smoke_check`
5. Run monthly calculations into `Agent Incentive Ledger`

## Important boundary

The app owns its required attribution fields, but reliable incentive calculations still
depend on verified Sales Invoice attribution and ERPNext collection data.

Run the app tests with:

```bash
bench --site yoursite run-tests --app agent_incentives
```
