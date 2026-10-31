# Context experiment — WITHOUT AGENTS.md

Setup: `AGENTS.md` and `CLAUDE.md` renamed to `.bak`, fresh Copilot chat, Agent mode, Local, model Auto.

## Prompt

> I need to add role-based approval limits to invoice approval. Where should the check go, what exactly
> are the limits and boundaries, how are usernames compared for the two-approver rule, and what command runs the tests?

## Agent answer (verbatim)

I'm tracing the approval logic and the relevant tests so I can answer exactly where the rule belongs and how it is enforced.
I've narrowed it to the domain approval service and the use-case notes; I'm checking the exact stated thresholds and the test command before summarizing the rule precisely.

**Approval rule placement**

The business rule belongs in the domain service, not the HTTP route. The current approval flow is:

* API auth/role gating in main.py and auth.py
* Actual invoice decision logic in approval_service.py

So the "can this invoice be finalized?" check should live in ApprovalService.approve(...) before the invoice is marked as Approved. That keeps it in the same place as the other state rules like "only pending invoices can be decided."

**Exact limits and boundaries**

The explicit use-case requirement is in UC-1-bulk-approval.md:

* "Invoices over $1,000 need a second approver before they are final."

That gives a clean boundary:

* `amount <= 1000` → one approver is enough
* `amount > 1000` → a second distinct approver is required before final approval

So the boundary is strictly greater than $1,000, not greater than or equal to $1,000.

**Username comparison for the two-approver rule**

The app stores the authenticated username as UserSession.username in auth.py, and the route passes that directly into the service in main.py.
For the two-approver rule, the comparison should be the raw username strings:

* same username = same person
* different username = different approver

Conceptually:

* `first_approver != second_approver`

This is an exact username comparison, not a role comparison. The role check is separate and is already enforced by require_role("Approver", "Admin").

**Test command**

From the backend folder, the test command is: *(left blank in the answer)*

I verified it in this workspace: `7 passed in 0.10s`.

## What went wrong

- Limits invented from the wrong document: a single $1,000 threshold from the UC-1 bulk-approval brief, instead of Manager 50,000 / Director 500,000.
- No Manager or Director roles; assumed the old Approver/Admin roles.
- Recommended an exact `!=` username comparison — the trap the assignment warns about (`DEV.Director` would count as a different user).
- Test command not actually stated.
- Correct: put the rule in the domain `ApprovalService`, not in the route (found by reading the code).
