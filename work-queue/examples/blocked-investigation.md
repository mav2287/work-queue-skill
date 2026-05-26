### WQ-021 Decide whether imported records need manager approval

- **Type**: investigation
- **Priority**: P2
- **Created**: 2026-05-23
- **Area**: import-workflow
- **Blocked on**: product decision about approval policy

**Problem / Want**
Imported records can be created automatically, but the desired approval policy is unclear. Implementation cannot be scoped until the owner decides whether manager approval is required.

**Acceptance**
- [ ] Confirm whether imported records require manager approval.
- [ ] Record the policy decision in the relevant project docs.
- [ ] If approval is required, open Ready implementation items for UI, permissions, tests, and audit logging.

**Notes**
**Local checks before asking**
- Searched the codebase for `manager_approval` and `approver_role`; no existing pattern.
- Read `docs/imports/README.md`; it does not mention approvals.
- Asked WORK_QUEUE.md for prior import-policy items; none found.

**Questions**
- Which imported records require approval, if any?
- Which role can approve them?
- What should happen when approval is denied?
