# Agent Incentive Workbench

Open /app/agent-incentive-workbench as System Manager.

## Configure and enroll

1. Open Settings. Choose the INR company, enable processing, and set new-plan defaults and rounding.
2. Add User in the workbench to create enrollment and an effective-dated plan together. Alternatively manage enrollment in Settings and plans through the plan list.
3. Choose salary × multiplier or a fixed threshold, the incentive percentage, and a month-start effective date.
4. A User may have only one active reward program: Agent Incentives OR WFH Commission. Both settings forms and WFH posting eligibility enforce this on the server. To switch programs, deactivate the old enrollment first. History is retained; disabling a User or an app does not release an active enrollment.
5. Set Incentive Agent on eligible Sales Invoices before submission. Invoice attribution is protected after submission/calculation. Historical owners are not inferred or backfilled automatically.

The app remains disabled/unconfigured until finance chooses settings. Installing it enrolls nobody and changes no WFH participation.

## Monthly earnings

Select the month and Refresh Calculations. Eligible allocations from submitted Receive Payment Entries count once, using payment posting date:

    eligible = max(payment entry received - monthly threshold, 0)
    incentive = eligible × rate / 100

Only the attributed invoice allocation counts, not the entire payment repeated for each agent. Invoice/customer/company/currency, duplicate allocations and amount caps are checked. Returns and refunds require review; credit notes are not automatically subtracted.

Open months show provisional earnings. Resolve exceptions, then Finalize Period after month-end. Preview confirmation freezes the calculation and receipt evidence; it creates no payment or accounting entry. Refresh cannot replace finalized evidence. Sources changing later produce review warnings.

Lifetime finalized earnings exclude open-month estimates and unreconciled legacy rows. Add a Record Reviewed Correction for an approved signed change to finalized earnings, with a review reason. Corrections are immutable; use a separately explained reversing correction instead of editing history.

## Paid amounts

Paid amounts come only from Agent Incentive Settlement allocations against submitted bank/cash Journal Entries. Configure a dedicated incentive payable account distinct from WFH's account. The debit row must use the supported User beneficiary and match the ledger agent. Its name is the Journal Entry Account child-row ID.

Use Record Verified Payment after accounting has recorded the real payment. Link its finalized incentive ledger, submitted Journal Entry, debit row and allocated amount. Partial payments are supported. Over-allocation, duplicate use, wrong parties, WFH vouchers and non-bank accrual journals are rejected. Cancelling the accounting voucher removes its paid contribution automatically.

This release does not create recognition Journal Entries, bank transfers or payroll. Accounting-backed Payout remains a separately scoped extension. A payment status field alone is not payment evidence.

## Agent analytics

Explicitly enrolled, enabled users see My Incentives in vobiz-agent-analytics:
- Payment Entry Received and remaining threshold for this month.
- Provisional/finalized period incentive.
- Lifetime finalized earnings, verified paid and outstanding.

These always belong to the signed-in user, regardless of call-date, team or selected-agent filters. Inactive participants can still see retained history. An unenrolled Administrator does not get a visibility bypass. No salary, bank details or clinical source information is returned by the self-view endpoint.

## Verification and deployment

- Offline tests: env/bin/python -W error -m unittest discover -s apps/agent_incentives/tests -q
- WFH regression tests: env/bin/python -W error -m unittest discover -s apps/wfh_commission/tests -q
- Hook coexistence: node apps/agent_incentives/tests/test_dashboard_hooks.js
- Syntax/schema check: env/bin/python apps/agent_incentives/tools/validate_workbench.py
- Rollback-only site check: env/bin/python apps/agent_incentives/tools/check_workbench_site.py
- Targeted metadata migration: tools/deploy_workbench.py (sriaas.local; take a backup first).
- Standard installation/migration also runs setup.install, adding attribution fields and indexes.

No automatic historical backfill or actual financial vouchers are part of deployment/testing. Use an isolated test site to exercise real accounting voucher submission before enabling payment operations.
