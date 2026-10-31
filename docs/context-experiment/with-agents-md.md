# Context experiment — WITH AGENTS.md

Setup: new `AGENTS.md` (Python version with approval rules R1–R7), `CLAUDE.md` = `@AGENTS.md`,
`.github/copilot-instructions.md` pointing to it. No agents/skills/hooks yet. Fresh Copilot chat, Agent mode, Local, model Auto.

## Prompt

> I need to add role-based approval limits to invoice approval. Where should the check go, what exactly
> are the limits and boundaries, how are usernames compared for the two-approver rule, and what command runs the tests?

## Agent answer (verbatim)

I'm confirming the approval rules in the project guidance and the relevant code so I can answer exactly where the check belongs and what the test command is.

**Approval check placement**

The approval-limit logic belongs in the domain layer, not in the API or UI. The project guidance in AGENTS.md says:

* business rules live under the domain layer
* the pure policy function is `evaluate_approval(invoice, approver) -> ApprovalDecision`
* the service evaluates that policy before building any new state and only then writes through the repository

So the "is this approver allowed for this amount?" check should happen before any invoice mutation or repository update.

**Limits and boundaries**

From the rules in AGENTS.md:

* Manager: allowed when `amount <= 50,000.00` inclusive
* Director: allowed when `amount <= 500,000.00` inclusive
* If `amount > 500,000.00`, approval needs two approvers
  * first approver may be a Manager or Director
  * second approver must be a Director
  * after the first valid approval, the invoice moves to `AwaitingSecondApproval`
  * only a Director on the second approval makes it `Approved`
* Admin cannot approve

Boundary expectations:

* `50,000.00` is allowed for a Manager
* `50,000.01` is not allowed for a Manager
* `500,000.00` is allowed for a Director
* `500,000.01` requires another approver

**Username comparison for the two-approver rule**

The rule says the same user must never count twice. The comparison is done:

* trim whitespace
* compare case-insensitively

In other words, normalize each username before comparing, so values like `demo.director`, `DEMO.DIRECTOR` and `demo.director` with different casing are treated as the same person.

**Test command**

From the commands section in AGENTS.md, the project test command is: `cd backend && pytest`.
That is the command to run the unit tests from the repo root.
