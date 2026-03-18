  Folosește Opus, max effort. Citește TOATE fișierele din proiect înainte de orice acțiune.

  MECANISME DISPONIBILE pe care le ai la dispoziție și pe care trebuie să le folosești unde e cazul:

  1. CLAUDE.md (rădăcina proiectului) — citit automat la fiecare mesaj. Trebuie ținut sub 200 rânduri. Conține doar esențialul: overview,  
  status, key files, conventions. Restul regulilor se mută în .claude/rules/.

  2. .claude/rules/*.md — fișiere citite AUTOMAT la fiecare mesaj, toate. Aici merg regulile detaliate, separate pe domeniu (decizii       
  permanente, reguli auto-update, arhitectură, roadmap status). Organizează logic — un fișier per subiect.

  3. CLAUDE.md nested în subdirectoare (backend/CLAUDE.md, frontend/CLAUDE.md) — citite automat când se lucrează pe fișiere din acel       
  folder. Conțin reguli specifice acelui folder (cum adaugi modul backend, cum adaugi pagină frontend, pattern-uri locale).

  4. Memory files (~/.claude/projects/C--Proiecte-NOU-Calculator-Pret-Traduceri/memory/) — citite automat prin index MEMORY.md. Doar       
  pentru: feedback utilizator, preferințe, referințe externe. NU pentru reguli sau status.

  5. Hook SessionStart (în .claude/settings.local.json) — rulează automat la deschiderea fiecărei sesiuni noi. Folosește-l pentru a afișa  
  statusul proiectului instant, fără ca AI-ul să trebuiască să citească manual fișiere.

  6. Hook Stop (în .claude/settings.local.json) — rulează automat la închiderea sesiunii. Folosește-l pentru auto-update documentație la   
  finalul fiecărei sesiuni (roadmap, PLAN_EXECUTIE, status).

  7. Hook PostToolUse pe Edit|Write (în .claude/settings.local.json) — rulează automat după fiecare editare de fișier. Folosește-l pentru  
  verificări automate (URL-uri hardcoded, migrări DB lipsă, etc.).

  8. Hook PreCompact (în .claude/settings.local.json) — rulează înainte de compactarea contextului. Folosește-l pentru a salva informații  
  critice care nu trebuie pierdute la compactare.

  9. .claude/commands/*.md — comenzi slash custom invocate manual (/update-docs, /pre-wave, /test-guide). Definește comenzi pentru
  operațiuni repetitive.

  10. .claude/agents/*.md — agenți dedicați cu prompt propriu și tool-uri restricționate. Creează un agent care veghează regulamentul,     
  validează reguli noi, și loghează modificările.

  IMPORTANT:
  - Implementează TOATE mecanismele de mai sus acolo unde au sens pentru cerințele din mesajul de mai jos
  - Organizează totul conform logicii tale — nu îți dictez structura exactă, tu ai contextul complet al proiectului
  - Fiecare mecanism implementat trebuie argumentat: de ce l-ai ales, ce rezolvă, cum funcționează
  - Hook-urile trebuie testate și funcționale pe Windows 10 cu bash (Git Bash)
  - La final prezintă-mi lista completă cu toate fișierele create/modificate și ce face fiecare
  - Toate scripturile trebuie să fie idempotente (pot rula de 100 de ori, același rezultat)
  - Păstrează settings.local.json existentă (merge cu permisiunile deja configurate acolo)
  - Pentru orice neclaritate — AskUserQuestion, nu presupune

    CERINȚELE MELE:

  1. Adaugă ca regulă permanentă în .claude ca la finalizarea fiecărei faze implementate să îmi prezinți într-un fișier modalitatea de     
  testare a fiecărei funcții atât pe web cât și pe telefon. Fișierul precum și celelalte din proiect trebuie actualizat după fiecare       
  rulare.

  2. Confirma implementarea și apoi livrează în chat o listă cu TOATE regulile din .claude să le văd clar și să pot efectua modificări unde   e cazul. Pe urmă la sfârșitul mesajului vreau să îmi menționezi părerea ta despre regulile existente — dacă au logică și mă ajută, ce ai   modifica tu, și aștept eventuale completări sau sugestii.

  3. Analizează toate fișierele existente din folderul principal și din 99_Roland_Work_Place. Care din informații sunt utile, ce se poate  
  unifica sau elimina, care fișiere sunt redundante sau cauzează confuzie. Creează un fișier în 99_Roland_Work_Place cu analiza completă.  
  Apoi propune o reorganizare logică — dar NU executa reorganizarea fără confirmarea mea.

  4. După restructurare, toate fișierele trebuie actualizate automat cu: orice plan întocmit, execuții efectuate, decizii pentru fiecare   
  fază, testările și validările, log activ, etc.

  5. Intocmește un agent sau o regulă permanentă prin care la fiecare solicitare a mea care face referire la modificare/extindere
  regulament, AI-ul din terminal să adapteze regula mea conform logicii lui (incât să nu apară confuzii), să îmi prezinte implementarea, și   să salveze execuția într-un log — să pot oricând verifica modificările pe tot parcursul proiectului în orice terminal sau sesiune.      

  6. Scopul principal: orice AI Claude Code din orice terminal sau sesiune alocat în acest proiect să aibă actualizat în permanență        
  statusul live al proiectului, harta completă, deciziile incluse — încât să nu trebuiască în fiecare terminal nou să recitească toată     
  documentația și să regândească tot sistemul.

  Activează și folosește MCP sequential-thinking și orice tool sau skill consideri necesar.


Info: mai jos iti trimit si textul ciorna in care mi-am notat ideile inainte sa iti formulez solicitarea:
** adaauga ca regula permanenta in .claude ca doresc sa finalizarea fiecarei faze implementate sa imi prezinti intr-un fisier modalitatea   
  de testare a fiecarei functii atat pe web cat si pe telefon .fisierul precum si celelalte din proiect trebuie actualizat dupa fiecare    
  rulare . confirma implementarea si apoi livreaza in chat o lista cu toate regulile din .claude sa le vad clar si sa pot efectua
  modificari unde e cazul . pe urma la sfarsitul mesajului vreau sa imi mentioneazi parerea ta despre regulile existente, daca au logica   
  si ma ajuta , ce ai modifica tu si aastept eventuale completari sau sugestii. **

Activeaza si foloseste MCP sequential-thinking si orice tool sau skill consideri necesar pentru aceasta executie prezentata mai jos : 

Include in analiza precedenta de mai sus marcata cu ** ... ** si fisierele din folderul principal: c:\Proiecte\NOU_Calculator_Pret_Traduceri\PLAN_EXECUTIE.md ,
  c:\Proiecte\NOU_Calculator_Pret_Traduceri\CLAUDE.md si c:\Proiecte\NOU_Calculator_Pret_Traduceri\Competitori.md si toate fisierele       
  existente in folderul: C:\Proiecte\NOU_Calculator_Pret_Traduceri\99_Roland_Work_Place . refa analiza precum ti-am cerut in mesajul       
  anterior si creaza un fisier in folder 99_Roland... in care sa o adaugi ca sa pot analiza . suplimentar mai vreau sa imi analizezi       
  fisierele mentionate , care din informatii sunt utile , ce se poate unifica sau elimina din ele , apoi sa imi mentionezi dupa logica o   
  reorganizare . unele din fisiere sunt ciorne de lucru ale mele,notite pt documentarea mea.  vreau sa elimin eventualele dubluri ,        
  fisiere redundante sau care cauzeaza confuzie. dar imi doresc ca dupa restructurare toate fisierele sa fie actualizate automat cu orice  
  plan intocmit , executii efectuate , decizii pt fiecare faza , testarile si validarile , log activ , etc . adauga sugestii elementare    
  si care sa fie utile cu adevarat pt ceea ce doresc eu si ceea ce am incercat sa mentionez in acest regulament .claude  .

  PS.  Se poate intocmi un agent cu rulare permanenta si automata in acest proiect care sa vegheeze in permanenta fisierul .claude si sa   
  remedieze eventualele reguli gresite care s-ar putea sa le mai cer , sau sa intocmesti o regula in .claude prin care sa mentionam clar   
  ca la fiecare solicitare de-a mea care face referire la modificare/extindere regulament , AI-ul din terminal sa adapteze regula mea      
  conform logicii lui incat sa nu apara confuzii si sa imi prezinte aceasta implementare si sa salveze executia lui intr-un log , sa pot   
  oricand sa verific modificarile pe tot parcursul proiectului in orice terminal sau sesiune .

  INTREBARE : in afara de fisierul .claude , crezi ca ar mai fi util sa modificam/actualizam si alte fisiere existente? sau daca ar fi     
  util sa creem si alte fisiere noi care sunt citite automat de AI-ul din terminal la fiecare rulare / sesiune pt informare si regulament  
  .

  Important: as vrea pot face ca orice AI claude code din orice terminal sau sesiune alocat in acest proiect sa aiba in memoria lui        
  actualizat in permanenta cu statusul live al proiectului, cu harta completa, cu deciziile incluse, etc incat sa nu trebuiasca in         
  fiecare  terminal nou sa reciteasca toata documentatia existenta si sa regandeasca tot sistemul , deoarece pierd timp si exista in       
  permanenta riscul de a nu continua de unde am ramas anterior si nici sa nu mai detina contextul pe care l-am avut interminalul           
  precedent.    Exemplu clar: (daca deschid acum un terminak nou in acest proiect, cu siguranta nu o sa stie tot ce sti tu despre          
  dorintele mele si detaliile stabilite deoarece nu detine contextul pe care il avem noi in terminalul curent). tocmai aceste lucruri      
  vreau sa le reglementez si pt care imi doresc sa imi oferi cele mai bune sugestii, imbunatatiri si completari , toate argumentate        
  detaliat , specificata utilitatea , modul de lucru ideal dintre noi .
