# Does AGENTS.md matter? Same question, fresh chat, with and without context

Prompt (identical both times):

> I need to add role-based approval limits to invoice approval. Where should the check go, what exactly
> are the limits and boundaries, how are usernames compared for the two-approver rule, and what command runs the tests?

| Question | Without AGENTS.md | With AGENTS.md |
|---|---|---|
| Where does the check go? | `ApprovalService.approve` (found by reading code) | Domain layer, in a pure `evaluate_approval` policy, evaluated **before** any mutation or repository write |
| Limits | Invented: single $1,000 threshold from the unrelated UC-1 brief | Manager ≤ 50,000.00, Director ≤ 500,000.00, two approvers above 500,000.00 |
| Boundaries | `> 1000` needs a second approver | 50,000.00 ✔ / 50,000.01 ✘ for Manager; 500,000.00 ✔ / 500,000.01 needs a second approver |
| Two-approver flow | "a second distinct approver", any role | First Manager or Director → `AwaitingSecondApproval`; second must be a Director |
| Roles | Assumed old Approver/Admin roles | Manager, Director; Admin cannot approve |
| Same-user comparison | Exact `!=` string compare — the trap the brief warns about | Trim + case-insensitive (`DEMO.DIRECTOR` = `demo.director`) |
| Test command | Not stated | `cd backend && pytest` |

**Conclusion:** without context the agent confidently built the wrong rule from the nearest document it could find
(a $1,000 limit from UC-1) and recommended the exact-match username comparison that would let the same person approve twice.
With AGENTS.md it got every limit, boundary, role and the normalised username comparison right, named the correct layer
and the "check before mutating" order, and gave the right test command. Both answers took one prompt; only the context changed.

One thing context did not fix by itself: the "with" answer describes `evaluate_approval` as if it already exists — it is
the planned design from AGENTS.md, not current code. The spec and tests still have to hold the line.

Raw answers: [without](without-agents-md.md) · [with](with-agents-md.md)
