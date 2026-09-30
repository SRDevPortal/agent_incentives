# Agent Incentives

Frappe/ERPNext application for monthly threshold-based incentives on submitted Receive Payment Entry allocations.

- Finance workbench: /app/agent-incentive-workbench
- Explicit enrollment and per-user effective plans
- Mutually exclusive active enrollment with WFH Commission
- Receipt evidence, provisional refresh and month-end finalization
- Immutable reviewed corrections and verified partial-payment tracking
- Self-only My Incentives cards in vobiz-agent-analytics

See [the operator guide](docs/WORKBENCH.md) for configuration, source attribution, payment verification and test commands.

Installation/migration adds app-owned invoice attribution fields and indexes. No users are automatically enrolled and no historical attribution or accounting entries are generated. Processing starts after finance configures Settings.

Accounting recognition Payout, bank transfers and payroll are outside this release; settlement tracking verifies already submitted accounting payments.
