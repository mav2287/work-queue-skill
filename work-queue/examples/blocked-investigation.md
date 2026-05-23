### WQ-021 Determine whether invoices must support partial refunds

- **Type**: investigation
- **Priority**: P2
- **Created**: 2026-05-23
- **Area**: billing
- **Blocked on**: product decision about refund policy

**Problem / Want**
Support received requests for partial refunds, but the current billing policy only mentions full refunds. Implementation cannot be scoped until the product and finance decision is clear.

**Acceptance**
- [ ] Confirm whether partial refunds are supported.
- [ ] Record the decision in the billing policy docs.
- [ ] If supported, open Ready implementation items for UI, payment provider integration, tests, and audit logging.

**Notes**
**Questions**
- Are partial refunds allowed for all products or only subscription purchases?
- Who can issue a partial refund?
- Does the customer receive a revised invoice?
