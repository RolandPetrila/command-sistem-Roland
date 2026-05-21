# Audit outputs (gitignored)

Rezultate auto-generate de skill-uri: `/audit`, `/security-review`, `/perf`, `/improve`.

## De ce gitignored

- Volume mare (rapoarte 50-200KB)
- Regenerabile (`/audit` re-runs)
- Date momentane (depasite la urmatorul commit)

## Ce sa pastrezi

Daca un audit dezvaluie URGENT/HIGH issues → muta concluziile in:
- `.workspace/investigations/` (RCA dedicat)
- `docs/plan.md` follow-ups
- `.meta/decisions.yaml` (daca devine decizie)

Apoi sterge raportul brut din `audit-outputs/`.
