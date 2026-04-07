# Agent Incentives - Plug-and-Play Status

## Completed
- settings single doctype
- incentive plan doctype
- incentive run doctype
- incentive ledger doctype
- formula helper functions
- setup status API
- smoke-check API
- install documentation
- settings single bootstrap helper

## Plug-and-play interpretation
This app is plug-and-play from the **application/code side**:
- it can be installed cleanly
- doctypes exist
- settings surface exists
- setup validation helpers exist
- docs exist

## Remaining practical boundary
Real incentive correctness still depends on:
- frozen attribution fields existing in the ERP app
- reliable payment/credit note source data
- a calculation runner using the business rules consistently

## Meaning of complete here
- code-side settings/plan/ledger structure is ready for install/UAT
- validation surface exists
- docs exist

## Meaning of not assumed
- no full monthly calculation engine added in this hardening pass
- no ERP-side attribution field installer added in this hardening pass
