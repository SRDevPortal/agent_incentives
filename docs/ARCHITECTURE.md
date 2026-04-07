# Agent Incentives Architecture

## Order of build
1. Frozen attribution fields
2. Incentive Settings
3. Agent Incentive Plan
4. Monthly calculation / ledger
5. Credit note deduction handling

## Frozen attribution fields (recommended in ERP app)
### Patient Encounter
- incentive_agent
- incentive_agent_name
- incentive_locked

### Sales Invoice
- source_encounter
- incentive_agent
- incentive_agent_name

## Incentive ownership rule
Always attribute incentive to the original sales agent who created the source encounter.
Doctor edits, dispatch-created invoices, and accounts-created payment entries must not change incentive ownership.

## Formula
- gross_collected = total eligible payments in period
- credit_note_amount = total credit note deductions in period
- net_collected = gross_collected - credit_note_amount
- threshold_amount = fixed amount or salary × multiplier
- eligible_amount = max(net_collected - threshold_amount, 0)
- payout_amount = eligible_amount × incentive_percentage

## Period basis recommendation
Use Payment Entry posting period for collections and Credit Note posting period for deductions.
