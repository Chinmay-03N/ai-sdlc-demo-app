# Surviving mutants — after hardening (126 mutants, 121 killed, 5 survived = 96.0%)

All 5 survivors are in the same branch of `evaluate_approval` (approval_policy.py):

    if approver.role not in {Role.MANAGER, Role.DIRECTOR}:
        return ApprovalDecision(False, f"Role {role_name} cannot approve invoices.")

| Mutant | Change | Verdict |
|---|---|---|
| mutmut_10 | `False` -> `None` | Equivalent — unreachable branch |
| mutmut_11 | reason -> `None` | Equivalent — unreachable branch |
| mutmut_12 | arguments dropped | Equivalent — unreachable branch |
| mutmut_13 | reason argument removed | Equivalent — unreachable branch |
| mutmut_14 | `False` -> `True` | Equivalent — unreachable branch |

**Why unreachable:** `Role` has only Manager, Director and Admin. Admin is refused by the `if` just above, so this
branch can never execute. No test can kill these mutants; writing one would mean testing impossible input.

**Action:** the duplicate Admin check is review finding L2. Merging both checks into a single
`if approver.role not in APPROVER_ROLES` removes the dead branch (the Admin tests then exercise it). Fixed in the review-fixes commit.