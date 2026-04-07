# Install Agent Incentives

## Bench install

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app /Users/admin/.openclaw/workspace/agent_incentives
bench --site yoursite install-app agent_incentives
bench --site yoursite migrate
bench --site yoursite clear-cache
```

## First-run steps

1. Add frozen attribution fields into the ERP app (`Patient Encounter`, `Sales Invoice`).
2. Configure `Agent Incentive Settings`.
3. Create one active `Agent Incentive Plan` per sales agent.
4. Verify setup using:
   - `/api/method/agent_incentives.api.setup.get_setup_status`
   - `/api/method/agent_incentives.api.setup.smoke_check`
5. Run monthly incentive calculations into `Agent Incentive Ledger`.

## Practical note
This app provides the configuration and ledger structure, but the actual source-of-truth collection math still depends on your ERP data model and attribution discipline.
