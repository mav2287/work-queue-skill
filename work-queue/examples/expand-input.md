# PRD: Invoice list improvements

**Author:** product
**Date:** 2026-05-20
**Status:** approved

## Background

The invoice list page (`apps/web/invoices/list.tsx`) was built before
the new design system landed. It does not handle the zero-invoice
case, sorts incorrectly when invoices share a date, and renders a
broken-looking row when the customer's display name is empty. Support
has fielded ~15 tickets in the last quarter that trace back to one of
these three issues.

## Goals

1. Users with no invoices should see the standard empty state, not a
   persistent loader.
2. Invoices sharing a `created_at` date should sub-sort by `id`
   descending so the order is deterministic across reloads.
3. Invoices with a blank customer name should render the customer's
   email address as a fallback instead of the empty `<div>` they
   render today.
4. Add a manual zero-invoice account to QA's fixture set so the empty
   state ships under test coverage.

## Non-goals

- Redesigning the row layout.
- Server-side sort changes — the fix is entirely client-side.

## Open questions

- Should the empty state link to "create invoice" or to the import
  flow? Product has not decided.
