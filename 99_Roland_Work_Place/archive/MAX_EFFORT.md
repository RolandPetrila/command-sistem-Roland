Obiectiv: Analizează critic planul de extindere al proiectului și evaluează dacă structura, ordinea și conținutul sunt optime pentru     
  implementare reală cu Claude Code. Dacă ceva trebuie regândit — propune, dar NU modifica nimic fără confirmarea mea.

  Citește OBLIGATORIU aceste fișiere ÎNTÂI (în această ordine):
  1. CLAUDE.md — context proiect, stack, status curent
  2. PLAN_EXECUTIE.md — ce s-a implementat deja, ce e marcat DONE
  3. 99_Roland_Work_Place/0.0_PLAN_EXTINDERE_COMPLET.md — planul complet de extindere (Fazele 8-18)
  4. 99_Roland_Work_Place/Documentare_Extindere_Proiect.md — deciziile și motivările din discuția de clarificare

  Features selectate pentru implementare (din HTML selector):
  [LIPEȘTE AICI LISTA GENERATĂ DIN HTML] - doresc sa selectezi primele functii pt implementare initiala , pe urma vom stabili restul functiilor dupa ce platforma functioneaza .

  Analizează planul PRIORITAR prin prisma acestei selecții — ce am bifat trebuie să fie coerent și implementabil în ordinea corectă.       

  Ce vreau de la tine:

  PAS 1 — AUDIT PLAN:
  Parcurge fiecare fază (8-18) și fiecare task individual. Pentru fiecare, evaluează:
  - E logic plasat în această fază? Ar trebui mutat?
  - Dependințele sunt corecte? Lipsesc pre-condiții?
  - Ordinea de implementare din tabelul PRIORITĂȚI RECOMANDATE reflectă realitatea?
  - Există task-uri care se suprapun sau se contrazic între faze diferite?
  - Lipsește ceva critic care ar bloca implementarea?

  PAS 2 — LISTA OBSERVAȚII:
  Prezintă-mi o listă structurată cu toate observațiile, grupate pe categorii:
  - [REORDONARE] — task-uri care ar trebui mutate în altă fază sau altă ordine
  - [LIPSĂ] — elemente care lipsesc și sunt necesare logic
  - [REDUNDANT] — task-uri duplicate sau care se suprapun
  - [DEPENDINȚĂ] — dependințe lipsă sau greșite între faze/task-uri
  - [ÎMBUNĂTĂȚIRE] — formulări neclare, criterii de done lipsă, estimări nerealiste
  - [OK] — faze/secțiuni care sunt corecte și nu necesită modificări

  Pentru fiecare observație: explică CE propui, DE CE, și ce IMPACT ar avea.

  PAS 3 — VERIFICARE COERENȚĂ GLOBALĂ:
  - Stack-ul rămâne fix (FastAPI + React + SQLite + Tailwind)?
  - Bugetul zero abonamente noi e respectat peste tot?
  - Structura modulară (backend/modules/ + frontend/src/modules/) e consistentă?
  - Baza de date COMUNĂ (nu per modul) e reflectată corect?
  - Estimările de sesiuni sunt realiste raportat la complexitate?

  Constrângeri:
  - NU modifica niciun fișier — doar analizează și prezintă
  - NU presupune ce vreau — dacă ai neclarități, folosește AskUserQuestion
  - NU simplifica planul — vreau analiza completă, nu rezumat
  - Dacă consideri că planul e bun așa cum e — spune explicit "faza X — fără modificări necesare"
  - Orice propunere de schimbare necesită confirmarea mea explicită ÎNAINTE de execuție

  La final: rezumă în 5-10 rânduri — câte observații ai găsit, câte faze sunt OK, care e cea mai importantă schimbare propusă.