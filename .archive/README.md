# Archive — Documente si Artefacte Deprecated

> Aceasta zona pastreaza documente, log-uri si scripturi vechi care nu mai sunt active dar nu se sterg pentru istoric. Conform principiului P7 din blueprint Native Workspace (arhiva over delete).

## Continut

| Item                                 | Provenienta                                                             | Data arhivare |
| ------------------------------------ | ----------------------------------------------------------------------- | ------------- |
| `roland_backend.log`                 | Runtime log capture (Faza 34)                                           | 2026-05-21    |
| `roland_start.log`                   | Runtime start log (Faza 34)                                             | 2026-05-21    |
| `update_tracking.py`                 | Script vechi tracking progres (Faza 0-8)                                | 2026-05-21    |
| `SABLOANE_SI_HINTURI_RECOMANDATE.md` | Sabloane Faza 20 (depasit)                                              | 2026-05-21    |
| `PLAN_EXECUTIE.md`                   | Plan executie Faza 0-8 (deprecated dupa restructurare Native Workspace) | 2026-05-21    |
| `.codex_global_staging/`             | Staging Codex (neutilizat)                                              | 2026-05-21    |
| `.claude-outputs/`                   | Output capture Claude vechi                                             | 2026-05-21    |

## Regula recuperare

Daca un fisier de aici devine relevant din nou:

1. Verifica daca exista versiune mai noua in `docs/` sau in proiect
2. Daca nu, copiaza inapoi in locatia originala
3. Documenteaza recuperarea in PLAN curent

## NU comit aici

`.archive/` e tracked partial (README + .md-uri istorice), DAR:

- Log-uri runtime → ignorate prin `.gitignore`
- `.codex_global_staging/`, `.claude-outputs/` → ignorate
- Documentele istorice (`SABLOANE_*`, `PLAN_EXECUTIE.md`) → TRACKED (decizii arhitecturale)
