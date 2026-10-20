# Planted Defects

Deliberate issues in `samples/specs/`, used to sanity-check audit runs.
This file is the answer key — it is never given to the model.

| # | File | Issue | Type |
|---|------|-------|------|
| 1 | checkout.md | "greater than 0 and less than 1" cannot be satisfied | Logical error |
| 2 | checkout.md | Reference to "section 4.2" which does not exist | Broken reference |
| 3 | checkout.md | "must respond quickly" has no measurable threshold | Ambiguity |
| 4 | checkout.md | Payment section defines no failure or timeout path | Incompleteness |
| 5 | checkout.md / pricing.md | Free shipping threshold is RM100 in one file, RM150 in the other | Inconsistency |
| 6 | pricing.md | RM100 falls into both the "over RM100" and "between RM50 and RM100" tiers | Logical error |
| 7 | pricing.md | Promotional codes both do and do not stack with tier discounts | Inconsistency |
| 8 | accounts.md | Email field length of 10 cannot hold the required name@domain.tld format | Inconsistency |
| 9 | accounts.md | Phone is mandatory in the registration table and optional in the profile section | Inconsistency |
| 10 | all | "user", "customer", and "shopper" used interchangeably with no definition | Terminology |


