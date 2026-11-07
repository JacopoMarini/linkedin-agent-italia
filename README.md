# LinkedIn Agent Italia

Tredici skill per Claude che gestiscono un account LinkedIn **in italiano**.
Gratis, licenza MIT, nessuna iscrizione, nessuna chiave API, niente da collegare.

Una scrive i post partendo da 21 formule di apertura. Una commenta i post degli
altri. Una gestisce le risposte sotto i tuoi. Una dà un voto al profilo su 100
e riscrive quello che perde punti. Una pianifica la settimana tenendo conto di
agosto, dei ponti e del fuso orario del tuo pubblico.

E una è l'**umanizzatore italiano**, il motivo per cui le altre sono usabili.
Toglie le lineette lunghe, i caratteri invisibili e i cliché che l'IA usa in
italiano ("in un mondo in continua evoluzione", "sono entusiasta di
annunciare", "gioca un ruolo fondamentale", gli elenchi di ✅), poi valuta
quello che resta con cinque controlli prima che tu lo veda.

**Non si pubblica niente finché non dici sì.** Queste skill scrivono. Pubblichi tu.

## Perché una versione italiana

Il progetto originale, [linkedin-agent-skill](https://github.com/Jakeschincariol/linkedin-agent-skill)
di Jake Schincariol, è ottimo ed è pensato per l'inglese. Su un testo italiano
pieno di cliché da IA, il suo rilevatore trova **0 parole stock e 0 strutture**,
perché cerca "delve" e "it's not just X, it's Y", conta le contrazioni inglesi
e legge solo lettere senza accenti.

Questa versione è stata riscritta da capo per l'italiano:

| | originale | Italia |
| --- | --- | --- |
| Lessico dei cliché | 113 voci inglesi | 127 voci italiane + quelle inglesi originali |
| Strutture segnalate | 11, inglesi | 16, italiane (anche gli elenchi di ✅ e "Sono orgoglioso di condividere") |
| Lingua | solo inglese | italiano e inglese, riconosciuta in automatico |
| Accenti, apostrofi, «» | non gestiti | gestiti; l'apostrofo dell'iPhone (’) non è penalizzato |
| Genere e numero | n/d | gli aggettivi variabili vengono segnalati, non sostituiti a caso |
| Voce | conta le contrazioni | conta prima e seconda persona e registro parlato |
| Calendario | generico | agosto, ponti, Natale, fuso del pubblico |
| Tu o Lei | n/d | in voce.md, rispettato da tutte le skill |
| Dati personali | n/d | regole di minimizzazione (GDPR) in messaggi e casella |
| Skill nuove | | `/li-bilingue`, `/li-dal-codice` |

## Installazione

Incolla questo in Claude:

```
https://github.com/JacopoMarini/linkedin-agent-italia

Installa queste skill, poi controlla che /li-post funzioni.
```

Oppure da solo, in Claude Code:

```bash
git clone https://github.com/JacopoMarini/linkedin-agent-italia.git
cp -r linkedin-agent-italia/skills/li-* ~/.claude/skills/
```

Oppure come plugin:

```
/plugin marketplace add JacopoMarini/linkedin-agent-italia
/plugin install linkedin-agent-italia
```

Per un solo progetto invece che globale: copia le stesse cartelle in
`.claude/skills/` del repository. Niente Claude Code? Incolla un singolo
`SKILL.md` all'inizio di una chat e funziona come modalità: perdi i due script
Python, che sono il cuore di `/li-umano`, ma il resto funziona.

Poi dedica dieci minuti a `templates/voce.md`. Copialo in
`~/.claude/linkedin/voce.md` e compilalo, oppure incolla tre tuoi post in Claude
e scrivi "fammi il mio voce.md da questi". Tutte le skill lo leggono. Se lo
salti, tutto esce con la voce di tutti gli altri.

Le skill hanno nomi italiani, quindi puoi installarle accanto al pacchetto
originale inglese senza conflitti.

## Le tredici

| comando | cosa fa |
| --- | --- |
| `/li-post` | Da un'idea a un post. Tre aperture dalle [21 formule](skills/li-post/hooks.json), una bozza completa, umanizzata prima che tu la veda. |
| `/li-commento` | Commenti ai post degli altri. Nove tipi, scelti in base al post. Mai "Ottimo post!". |
| `/li-risposte` | Le risposte sotto i tuoi post. Divide i commenti in cliente / sostanza / pari / supporto / rumore, poi scrive in quell'ordine. |
| `/li-profilo` | Voto al profilo con una [griglia di 12 voci](skills/li-profilo/rubrica.json) su 100, poi riscrive partendo da cosa perde più punti. |
| `/li-piano` | La settimana: cosa pubblicare, quando, e le 10 persone con cui interagire. Calendario italiano incluso. |
| `/li-umano` | L'umanizzatore. Due script che girano davvero. Vedi sotto. |
| `/li-carosello` | Post documento: testo slide per slide, la copertina che fa scorrere, il PDF da caricare. |
| `/li-riusa` | Un video, una newsletter o una trascrizione diventano una settimana di post, ognuno autonomo. |
| `/li-dm` | La nota d'invito da 200 caratteri, il primo messaggio e i due solleciti. Due. Con il tu o il Lei giusto. |
| `/li-inbox` | Smista la casella in cliente / recruiter / collega / richiesta / spam. Ai recruiter chiede RAL, contratto e modalità. |
| `/li-audit` | Analisi di quello che hai già pubblicato. Ordina per tasso di interazione, non per impressioni. |
| `/li-bilingue` | **Nuova.** Post nativi in italiano e in inglese (non tradotti), profilo in lingua secondaria, quale lingua per quale post. |
| `/li-dal-codice` | **Nuova.** Dal bug, dalla PR o dal refactoring a un post, togliendo prima tutto ciò che è del cliente o del datore di lavoro. |

## L'umanizzatore

`/li-umano` contiene due script Python senza dipendenze. Girano sul tuo
computer, sul tuo testo, e non caricano niente.

```bash
python3 umanizza.py bozza.txt --report      # ripulisce e mostra ogni modifica
python3 rileva.py bozza.txt                  # punteggio, cinque controlli
python3 rileva.py prima.txt dopo.txt         # dimostra il miglioramento
```

La lingua si riconosce da sola; per forzarla, `--lingua it` o `--lingua en`.

**Cosa sparisce in automatico:**

- **Caratteri invisibili.** Spazi a larghezza zero, word joiner, trattini
  morbidi, BOM, caratteri tag Unicode, spazi non separabili.
- **Tipografia.** Lineetta lunga → virgola, lineetta media → trattino,
  virgolette alte curve → dritte, puntini → tre punti. Le «virgolette basse»
  restano.
- **Il lessico.** "In un mondo in continua evoluzione" → "oggi", "gioca un
  ruolo fondamentale" → "conta molto", "sono entusiasta di annunciare" →
  "annuncio", "sinergia" → "collaborazione", "è importante sottolineare che" →
  via. Sta in [`lessico.it.json`](skills/li-umano/lessico.it.json) ed è fatto
  per essere modificato.

**Cosa viene segnalato invece che corretto:** gli aggettivi che cambiano con
genere e numero ("innovativo/a/i/e", "olistico", "trasformativo"), le frasi da
motivatore ("mettersi in gioco", "fare la differenza"), "Non è solo X, è Y",
"Il risultato?" su una riga, tre aggettivi in fila, gli elenchi di ✅, "In
conclusione", "Tu cosa ne pensi?", i muri di hashtag, le frasi tutte uguali.
Cambiare la forma di una frase richiede giudizio: viene restituita per essere
riscritta, non massacrata da una regex.

**I cinque controlli**, da 0 a 100, più alto è più umano:

| controllo | cosa misura |
| --- | --- |
| RITMO | variazione della lunghezza delle frasi. I modelli scrivono uniforme. |
| CONCRETEZZA | numeri, nomi, sigle, date ogni 100 parole |
| CLICHÉ | voci del lessico ogni 100 parole |
| IMPRONTA | caratteri invisibili, lineette lunghe, virgolette curve |
| VOCE | prima e seconda persona, registro parlato, strutture tipiche |

Il verdetto pesa la media al 60% e il **controllo più debole** al 40%, perché a
un rilevatore basta un segnale.

Su un post generato pieno di cliché:

```
  RITMO         ######################## 100.0
  CONCRETEZZA   #####################...  87.6
  CLICHÉ        ........................   0.0    17 cliché, 18.1 ogni 100 parole
  IMPRONTA      ##################......  74.4    1 lineetta lunga
  VOCE          ........................   0.0    8 strutture
  ------------------------------------------------------------
  UMANO         ########................  31.4   SEGNALATO
```

Dopo `umanizza.py`, con le strutture segnalate non ancora riscritte, sale
poco, ed è voluto: l'ultimo tratto tocca a te. Riscritto a mano partendo da una
storia vera:

```
  31.4 SEGNALATO  ->  95.1 PASSA   (+63.7)
```

In inglese i punteggi sono identici a quelli dello script originale, con una differenza voluta: il testo tra virgolette ("...", «...», “...”) è trattato come citazione e non viene né riscritto né contato. Un post che prende in giro "sono entusiasta di annunciare" non deve vederselo correggere. E una virgola seguita da un a capo ("Ciao Mario,") resta dov'è: l'originale la toglieva insieme alla riga vuota successiva.

## Le avvertenze, che sono la parte onesta

**Queste skill non pubblicano su LinkedIn, e non devono farlo.** Non esiste
un'API ufficiale per pubblicare su un profilo personale senza un'app partner
approvata, e automatizzare il sito con un browser o uno strumento di terze
parti viola il [Contratto di licenza di LinkedIn](https://www.linkedin.com/legal/user-agreement)
e fa limitare gli account. Quindi ogni skill finisce allo stesso modo: un
blocco pronto da copiare, e lo incolli tu. Non è un limite aggiunto dopo, è il
progetto.

**I cinque controlli sono euristiche locali, non rilevatori.** Sono modellati
sui segnali che usano i rilevatori pubblici e girano solo sul tuo computer. Non
sono GPTZero, Originality, Copyleaks, Winston o Turnitin, non chiamano quei
servizi e non possono promettere i loro verdetti. Sistemare quello che misurano
tende a spostare anche quei numeri, perché misurano le stesse cose. Questa è
tutta la promessa. Nessuno può venderti onestamente "non rilevabile".

**Il passaggio sui caratteri invisibili è reale ed è limitato.** Toglie i
caratteri a larghezza zero e di formato che finiscono nel testo generato e
sopravvivono al copia-incolla. Non pretende di aggirare schemi crittografici
di filigrana.

**Niente viene inventato.** Nessuna metrica, cliente o risultato inventato
sotto il tuo nome. Se una bozza ha bisogno di un numero che non hai dato,
torna con `{{il tuo numero}}` dentro e un avviso, sempre.

**Niente dati altrui in giro.** Le skill che leggono messaggi e commenti di
altre persone li usano per rispondere e non li archiviano. `/li-dal-codice`
toglie nomi di clienti, colleghi, URL interni e credenziali prima di scrivere.

## File

```
skills/li-post/hooks.json          21 formule di apertura: schema, esempio, a cosa serve, come si rovina
skills/li-umano/lessico.it.json    il lessico italiano: 127 voci, 16 strutture, caratteri invisibili
skills/li-umano/lessico.en.json    il lessico inglese originale
skills/li-umano/lingua.py          tutto ciò che dipende dalla lingua
skills/li-umano/umanizza.py        i tre passaggi di pulizia
skills/li-umano/rileva.py          il pannello dei cinque controlli
skills/li-profilo/rubrica.json     la griglia da 100 punti per il profilo
templates/voce.md                  il tuo profilo di voce. Compilalo per primo.
```

## Crediti

Adattamento italiano, umanizzatore italiano, `/li-bilingue` e `/li-dal-codice`
di **Jacopo Marini** ([GitHub](https://github.com/JacopoMarini)), parte di
[Dev Zero to Hero](https://www.skool.com/officina-ia-per-dev-9094), la community
di sviluppatori italiani che usano Claude sul lavoro vero.

Basato su [linkedin-agent-skill](https://github.com/Jakeschincariol/linkedin-agent-skill)
di **Jake Schincariol** ([opusjake.ai](https://opusjake.ai)), rilasciato con
licenza MIT.

## Licenza

MIT. Prendilo, cambialo, pubblicalo. Mantieni le due righe di copyright in
[`LICENSE`](LICENSE).

## Provalo in 30 secondi

```bash
cd linkedin-agent-italia
python3 skills/li-umano/rileva.py esempi/bozza-generata.txt esempi/bozza-riscritta.txt
```
