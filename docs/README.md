# Documentatie Roland Command Center

Narrative + referinte arhitecturale. Conform pattern Native Workspace, separat de cod LIVE si de zona personala user.

## Structura

| Folder/Fisier    | Continut                                                   |
| ---------------- | ---------------------------------------------------------- |
| `plan.md`        | Plan implementare curent (max 500 linii) — _generat in E3_ |
| `archive/`       | Faze anterioare detaliate (faze 0-32) — _generat in E3_    |
| `handovers/`     | Documente de transfer/handover intre sesiuni               |
| `audit-externe/` | Audit-uri din surse externe (Gemini, ChatGPT, etc.)        |
| `resume.md`      | Snapshot punct curent pentru reluare sesiune               |
| `todo.md`        | Roadmap actiuni manuale user + cod                         |

## Distinctie fata de alte zone

- **`docs/`** (acest folder) — narrative arhitectural si plan, citit zilnic
- **`99_Roland_Work_Place/`** — USER_WORKSPACE: notite personale, audit-uri, capturi
- **`.workspace/`** — zona asistent AI (drafts, investigations, audit-outputs) — _generat in E4_
- **`.archive/`** — documente deprecated, log-uri istorice
- **`.meta/`** — Single Source of Truth structurat (YAML) — _generat in E2_

## Navigare rapida

- Stare proiect → `.meta/status.yaml` (cand exista)
- Decizii arhitecturale → `.meta/decisions.yaml` (cand exista)
- Operatiuni urgenta → `../RUNBOOK.md` (cand exista, E6)
- Regulament Claude Code → `../CLAUDE.md` (slim)
