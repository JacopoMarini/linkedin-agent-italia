#!/usr/bin/env python3
"""
umanizza.py - toglie l'impronta da macchina da una bozza, in italiano o inglese.

Tre passaggi, in quest'ordine:

  1. INVISIBILI    cancella o normalizza i caratteri che una tastiera non
                   produce: spazi a larghezza zero, word joiner, trattini
                   morbidi, BOM, caratteri tag Unicode, spazi non separabili.
  2. TIPOGRAFIA    lineetta lunga -> virgola, lineetta media -> trattino,
                   virgolette curve -> dritte, puntini -> tre punti.
                   In italiano le «virgolette basse» restano dove sono.
  3. LESSICO       sostituisce i cliché del lessico con parole semplici,
                   rispettando maiuscole e senza toccare i link.
                   Le voci con "replace": null vengono solo SEGNALATE: in
                   italiano molti aggettivi cambiano con genere e numero
                   ("innovativo/innovativa/innovativi") e una sostituzione
                   automatica romperebbe la frase.

Le strutture ("Non è solo X, è Y", la domanda-rivelazione, gli elenchi di ✅)
vengono SEGNALATE, mai riscritte: cambiare la forma di una frase richiede
giudizio, quindi è lavoro del modello o tuo, non di una regex.

Uso
  python3 umanizza.py bozza.txt
  python3 umanizza.py bozza.txt --report
  python3 umanizza.py bozza.txt --lingua en --report
  pbpaste | python3 umanizza.py - --report
  python3 umanizza.py bozza.txt -o pulito.txt
  python3 umanizza.py bozza.txt --json
"""

import argparse
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lingua  # noqa: E402

URL_RE = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\S+")


def _cp(spec):
    if "-" in spec:
        a, b = spec.split("-")
        return (int(a[2:], 16), int(b[2:], 16))
    return int(spec[2:], 16)


def proteggi_url(text):
    trovati = []

    def stash(m):
        trovati.append(m.group(0))
        return f"\x00URL{len(trovati) - 1}\x00"

    return URL_RE.sub(stash, text), trovati


def ripristina_url(text, trovati):
    for i, url in enumerate(trovati):
        text = text.replace(f"\x00URL{i}\x00", url)
    return text


def passo_invisibili(text, lex):
    hits = []
    for voce in lex["invisible"]:
        cp = _cp(voce["cp"])
        if isinstance(cp, tuple):
            pattern = "[" + re.escape(chr(cp[0])) + "-" + re.escape(chr(cp[1])) + "]"
        else:
            pattern = re.escape(chr(cp))
        n = len(re.findall(pattern, text))
        if n:
            hits.append({"name": voce["cp"] + " " + voce["name"], "count": n,
                         "action": voce["action"]})
            text = re.sub(pattern, "" if voce["action"] == "delete" else " ", text)
    # Qualsiasi altro carattere di formato (Cf) è invisibile per definizione.
    # I segnaposto \x00 dei link sono Cc, non Cf, quindi restano.
    stray = [c for c in text if unicodedata.category(c) == "Cf"]
    if stray:
        hits.append({"name": "altri caratteri invisibili di formato", "count": len(stray),
                     "action": "delete"})
        text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return text, hits


def passo_tipografia(text, lex):
    hits = []
    for voce in lex["typographic"]:
        ch = voce["from"]
        n = text.count(ch)
        if not n:
            continue
        hits.append({"name": f"{ch} {voce['name']}", "count": n,
                     "to": voce["to"].strip() or "(spazio)"})
        if ch == "—":
            text = re.sub(r"\s*—\s*", ", ", text)
        elif ch == "–":
            text = re.sub(r"\s*–\s*(?=\d)", "-", text)      # 5–10 -> 5-10
            text = re.sub(r"\s+–\s+", ", ", text)            # usata come lineetta
            text = text.replace("–", "-")
        else:
            text = text.replace(ch, voce["to"])
    # Una virgola inserita prima di altra punteggiatura suona male.
    text = re.sub(r",\s*([,.;:!?])", r"\1", text)
    text = re.sub(r",\s*\n", "\n", text)
    return text, hits


def _stesse_maiuscole(src, repl):
    if not repl:
        return repl
    if src.isupper() and len(src) > 1:
        return repl.upper()
    if src[0].isupper():
        return repl[0].upper() + repl[1:]
    return repl


def passo_lessico(text, lex, lang):
    """Sostituisce cliché e frasi fatte. Le più lunghe prima, così le frasi
    vincono sulle singole parole. Le voci senza sostituto si segnalano soltanto."""
    hits, segnalate = [], []
    voci = sorted(lex["phrases"] + lex["words"], key=lambda e: len(e["find"]), reverse=True)
    for voce in voci:
        pattern = lingua.pattern_voce(voce["find"])
        trovate = pattern.findall(text)
        if not trovate:
            continue
        if voce.get("replace") is None:
            segnalate.append({"find": voce["find"], "count": len(trovate),
                              "family": voce["family"], "hint": voce.get("hint", "")})
            continue
        hits.append({"find": voce["find"], "replace": voce["replace"] or "(eliminata)",
                     "count": len(trovate), "family": voce["family"]})
        if voce["replace"] == "":
            # Cancellazione: lascio un segnaposto per sistemare la maiuscola dopo.
            text = pattern.sub("\x01", text)
        else:
            text = pattern.sub(lambda m, r=voce["replace"]: _stesse_maiuscole(m.group(0), r), text)
    # Se la cancellazione era a inizio frase, la parola che segue diventa maiuscola.
    text = re.sub(r"(^|[.!?]\s+|\n)\x01[ \t,]*([^\W\d_])",
                  lambda m: m.group(1) + m.group(2).upper(), text)
    text = text.replace("\x01", "")
    # Pulizia dopo le cancellazioni.
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"(?m)^[ \t]*([,.;:])\s*", "", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"(?m)^[ \t]+$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r",\s*(" + lingua.CONNETTIVI[lang] + r")\s*,\s*",
                  lambda m: ". " + m.group(1)[0].upper() + m.group(1)[1:] + ", ",
                  text, flags=re.IGNORECASE)
    return text, hits, segnalate


def scansiona_strutture(text, lex):
    flags = []
    for s in lex["structures"]:
        try:
            pattern = re.compile(s["regex"], re.MULTILINE)
        except re.error:
            continue
        trovate = pattern.findall(text)
        if trovate:
            flags.append({"name": s["name"], "count": len(trovate), "fix": s["fix"]})
    lens = [len(f.split()) for f in lingua.frasi(text)]
    if len(lens) >= 4:
        media = sum(lens) / len(lens)
        var = sum((n - media) ** 2 for n in lens) / len(lens)
        cv = (var ** 0.5) / media if media else 0
        if cv < 0.35:
            flags.append({
                "name": f"Frasi tutte della stessa lunghezza (variazione {cv:.2f})",
                "count": len(lens),
                "fix": "Spezza una frase a metà, lasciane correre un'altra. Le macchine scrivono uniforme.",
            })
    return flags


def umanizza(text, lex, lang):
    text, urls = proteggi_url(text)
    text, inv = passo_invisibili(text, lex)
    text, tipo = passo_tipografia(text, lex)
    text, lessi, segnalate = passo_lessico(text, lex, lang)
    text = ripristina_url(text, urls)
    return text.strip() + "\n", {
        "lingua": lang,
        "invisible": inv,
        "typographic": tipo,
        "lexical": lessi,
        "flagged_words": segnalate,
        "structures": scansiona_strutture(text, lex),
    }


def stampa_report(report, out=sys.stderr):
    def titolo(t):
        print(f"\n{t}\n" + "-" * len(t), file=out)

    totale = sum(h["count"] for k in ("invisible", "typographic", "lexical") for h in report[k])
    da_riscrivere = len(report["structures"]) + len(report["flagged_words"])

    titolo(f"REPORT UMANIZZA  (lingua: {report['lingua']})")
    print(f"{totale} tracce da macchina rimosse, {da_riscrivere} punti da riscrivere a mano", file=out)

    if report["invisible"]:
        titolo("1. CARATTERI INVISIBILI")
        for h in report["invisible"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['action']}", file=out)
    if report["typographic"]:
        titolo("2. TIPOGRAFIA")
        for h in report["typographic"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['to']}", file=out)
    if report["lexical"]:
        titolo("3. LESSICO SOSTITUITO")
        for h in report["lexical"]:
            print(f"  {h['count']:>3}x  {h['find']}  -> {h['replace']}   [{h['family']}]", file=out)
    if report["flagged_words"]:
        titolo("4. PAROLE DA RISCRIVERE  (non sostituite: genere, numero o senso cambiano)")
        for h in report["flagged_words"]:
            hint = f"  - {h['hint']}" if h["hint"] else ""
            print(f"  {h['count']:>3}x  {h['find']}   [{h['family']}]{hint}", file=out)
    if report["structures"]:
        titolo("5. STRUTTURE  (non corrette in automatico, riscrivile tu)")
        for h in report["structures"]:
            print(f"  {h['count']:>3}x  {h['name']}\n        {h['fix']}", file=out)
    if not (totale or da_riscrivere):
        titolo("PULITO")
        print("  Niente da togliere.", file=out)
    print("", file=out)


def main():
    ap = argparse.ArgumentParser(description="Toglie l'impronta da macchina da una bozza.")
    ap.add_argument("input", nargs="?", default="-", help="file, oppure - per stdin")
    ap.add_argument("-o", "--out", help="scrive qui il testo pulito invece che su stdout")
    ap.add_argument("--report", action="store_true", help="mostra cosa è cambiato (su stderr)")
    ap.add_argument("--json", action="store_true", help="emette {text, report} in JSON")
    ap.add_argument("--lingua", default="auto", choices=["auto", "it", "en"])
    ap.add_argument("--lessico", help="percorso di un lessico personalizzato")
    args = ap.parse_args()

    grezzo = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    lang = lingua.scegli_lingua(grezzo, args.lingua)
    lex = lingua.carica_lessico(lang, args.lessico)
    pulito, report = umanizza(grezzo, lex, lang)

    if args.json:
        print(json.dumps({"text": pulito, "report": report}, indent=2, ensure_ascii=False))
        return
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(pulito)
        print(f"scritto {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(pulito)
    if args.report:
        stampa_report(report)


if __name__ == "__main__":
    main()
