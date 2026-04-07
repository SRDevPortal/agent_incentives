# Agent Incentives - Smoke Test

## 1. Install and migrate

```bash
bench --site yoursite install-app agent_incentives
bench --site yoursite migrate
bench --site yoursite clear-cache
```

## 2. Setup status
Call:
```text
/api/method/agent_incentives.api.setup.get_setup_status
```
Expected:
- returns counts and recent plans

## 3. Smoke check
Call:
```text
/api/method/agent_incentives.api.setup.smoke_check
```
Expected:
- confirms settings, plan, run, and ledger doctypes exist
- returns formula helper reference

## 4. Settings sanity
- open `Agent Incentive Settings`
- save defaults
Expected:
- settings record saves cleanly

## 5. Plan sanity
- create one `Agent Incentive Plan`
Expected:
- record saves cleanly
- threshold fields validate

## 6. Formula sanity
- verify threshold and payout values using known examples
Expected:
- helper formulas align with the documented architecture
