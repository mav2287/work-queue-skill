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
Local checks before asking:
- Example only: replace with actual target-project searches, files, docs, or logs inspected before asking the user.

**Questions**
- Which imported records require approval, if any?
- Which role can approve them?
- What should happen when approval is denied?
