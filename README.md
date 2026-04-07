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

## Install

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app /Users/admin/.openclaw/workspace/agent_incentives
bench --site yoursite install-app agent_incentives
bench --site yoursite migrate
bench --site yoursite clear-cache
```

## First-run flow
1. Open `Agent Incentive Settings`
2. Configure threshold defaults and deduction behavior
3. Create one active `Agent Incentive Plan` per sales agent
4. Verify setup using:
   - `/api/method/agent_incentives.api.setup.get_setup_status`
   - `/api/method/agent_incentives.api.setup.smoke_check`
5. Run monthly calculations into `Agent Incentive Ledger`

## Important boundary
This app is plug-and-play from the code side for settings/plans/ledger structure, but real incentive calculation still depends on frozen attribution fields and ERP-side collection data being present and trustworthy.
