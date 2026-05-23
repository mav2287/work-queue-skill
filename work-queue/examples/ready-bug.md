### WQ-014 Show empty state when learner has no assignments

- **Type**: bug
- **Priority**: P1
- **Created**: 2026-05-23
- **Area**: learner-dashboard

**Problem / Want**
Learners with zero assignments hit `/dashboard/learner` and see a loading spinner forever. They should see the normal empty state and a link to browse available training.

**Acceptance**
- [ ] Learners with zero assignments see an empty state instead of a persistent spinner.
- [ ] Learners with active assignments still see the assignment list.
- [ ] The failure path is covered by a test or documented manual verification using a zero-assignment learner.

**Notes**
- Repro: log in as `learner-empty@example.com`, open `/dashboard/learner`.
- Relevant files: `app/dashboard/learner/page.tsx`, `app/_components/learner/AssignmentList.tsx`.
