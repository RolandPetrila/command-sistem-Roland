Am identificat următoarele probleme în planul de restructurare. Rezolvă-le în cadrul implementării:

  PROBLEME REZOLVABILE ACUM (în acest proiect):

  P1 — CONFLICT R-CLEAN + R-WORK din global vs proiect:
  - R-CLEAN și R-WORK din regulamentul global sunt scrise pentru folderul 00_Regulament_Claude_Code, nu pentru proiecte normale
  - R-WORK cere subfolder datat per execuție (YYYY-MM-DD_task/) dar proiectul pune fișiere direct în 99_Roland_Work_Place/
  - FIX: În .claude/rules/ adaugă o regulă clară că regulile de proiect din .claude/rules/ au PRIORITATE față de regulile globale când     
  există conflict. Menționează explicit că R-CLEAN și R-WORK din global NU se aplică în acest proiect — convențiile locale sunt definite în   CLAUDE.md și .claude/rules/.

  P2 — R-SYNC nu e relevant în acest proiect:
  - R-SYNC propagă modificări Claude → Gemini/Codex — doar pentru folderul de regulament
  - FIX: În .claude/rules/ adaugă notă: "R-SYNC din global — NU se aplică. Acest proiect nu are echivalent Gemini/Codex."

  P3 — R-SNAPSHOT nu e relevant în acest proiect:
  - R-SNAPSHOT caută PENDING_IMPLEMENTARI.md care nu există aici
  - FIX: În .claude/rules/ adaugă notă: "R-SNAPSHOT din global — NU se aplică. Tracking-ul se face prin PLAN_EXECUTIE.md și
  .claude/rules/roadmap."

  P4 — NU muta PLAN_EXECUTIE.md în archive:
  - E referit direct în CLAUDE.md, în memory, și în multiple conversații anterioare
  - PLAN_EXECUTIE.md rămâne în rădăcina proiectului. NU se arhivează.

  P5 — NU folosi git add -A:
  - Poate adăuga fișiere nedorite (.db, uploads/, node_modules/)
  - Folosește git add pe fișiere specifice, nu -A.

  P6 — Overhead protocol pre-implementare:
  - Între Regula Supremă (95% claritate), R-BRIEF, R-MODE, și regulile noi (02-pre-implementation) — sunt 4 nivele de "întreabă înainte"   
  - FIX: În 02-pre-implementation.md menționează explicit că briefing-ul per-proiect ÎNLOCUIEȘTE R-BRIEF și R-MODE din global pentru       
  task-urile din acest proiect. Un singur briefing, nu 3 suprapuse.

  REGULĂ NOUĂ DE ADĂUGAT:

  În .claude/rules/ (fișier separat sau în 05-rule-governance.md) adaugă:
  "PRIORITATE REGULI: Regulile din .claude/rules/ și CLAUDE.md per-proiect au PRIORITATE față de regulile din ~/.claude/CLAUDE.md global   
  atunci când există conflict direct. Regulile globale care sunt specifice folderului 00_Regulament_Claude_Code (R-CLEAN, R-WORK, R-SYNC,  
  R-SNAPSHOT) NU se aplică în alte proiecte."

  Implementează aceste fix-uri ca parte din restructurare, apoi confirmă ce ai rezolvat.