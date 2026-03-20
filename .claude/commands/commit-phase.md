# /commit-phase — Commit automat per faza implementata

Executa commit Git pentru faza curenta, cu mesaj standardizat.

1. Ruleaza `git status` — verifica ce fisiere sunt modificate
2. Filtreaza fisierele relevante (exclude `.env`, `*.db`, `node_modules/`, `__pycache__/`, `dist/`)
3. Grupeaza pe categorii: backend, frontend, docs, rules
4. Prezinta lista de fisiere si cere confirmare INAINTE de commit
5. Creeaza commit cu mesaj standardizat:
   ```
   Faza [N]: [Nume] — [rezumat 1 linie]

   Implementat:
   - [lista features principale]

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   ```
6. NU face push — doar commit local
7. Afiseaza `git log --oneline -3` la final pentru confirmare
8. NICIODATA `git add -A` — adauga fisiere specifice
