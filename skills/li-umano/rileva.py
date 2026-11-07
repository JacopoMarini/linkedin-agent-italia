#!/usr/bin/env python3
"""
rileva.py - un pannello di cinque controlli che stima quanto una bozza
sembra scritta da una macchina. Funziona in italiano e in inglese.

Cos'è:  cinque euristiche locali, modellate sui segnali che i rilevatori
pubblici misurano davvero: variazione della lunghezza delle frasi,
concretezza, lessico da cliché, impronta tipografica e voce. Ogni punteggio
è calcolato sul tuo computer, dal solo testo. Niente viene caricato online.

Cosa NON è:  GPTZero, Originality, Copyleaks, Winston o Turnitin. Non chiama
le loro API e non può promettere il loro verdetto. Misura le stesse cose su
cui si basano, ed è per questo che sistemarle tende a spostare anche i loro
numeri. L'unica promessa onesta è quella di questa riga.

Ogni controllo restituisce un punteggio UMANO da 0 a 100. Più alto è meglio.

Uso
  python3 rileva.py bozza.txt
  python3 rileva.py bozza.txt --lingua en
  pbpaste | python3 rileva.py -
  python3 rileva.py bozza.txt --json
  python3 rileva.py prima.txt dopo.txt      # confronta due bozze
"""

import argparse
import json
import os
import re
import statistics
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lingua  # noqa: E402

CONTROLLI = ["RITMO", "CONCRETEZZA", "CLICHÉ", "IMPRONTA", "VOCE"]


def clamp(n):
    return max(0.0, min(100.0, n))


def scala(valore, umano, macchina):
    """Porta valore su 0-100, dove `umano` -> 100 e `macchina` -> 0."""
    if umano == macchina:
        return 50.0
    return clamp((valore - macchina) / (umano - macchina) * 100)


def ctrl_ritmo(text, lang):
    """Le persone variano molto la lunghezza delle frasi. I modelli no."""
    lens = [len(f.split()) for f in lingua.frasi(text)]
    if len(lens) < 4:
        return 50.0, "troppo corto per giudicare"
    media = statistics.mean(lens)
    cv = statistics.pstdev(lens) / media if media else 0
    return scala(cv, umano=0.70, macchina=0.22), \
        f"variazione {cv:.2f} su {len(lens)} frasi (meglio 0,55+)"


def ctrl_concretezza(text, lang):
    """Numeri, nomi e dettagli concreti. Il testo generico è astratto."""
    w = lingua.parole(text)
    if len(w) < 25:
        return 50.0, "troppo corto per giudicare"
    per100 = 100 / len(w)
    hits = len(lingua.NUMERI[lang].findall(text)) + len(set(lingua.PROPRI.findall(text)))
    if lang == "it":
        hits += len(lingua.CONCRETI_IT.findall(text))
    densita = hits * per100
    return scala(densita, umano=6.0, macchina=0.5), \
        f"{hits} elementi concreti, {densita:.1f} ogni 100 parole (meglio 4+)"


def ctrl_cliche(text, lex):
    """Densità di cliché rispetto al lessico (anche le voci solo segnalate)."""
    w = lingua.parole(text)
    if not w:
        return 50.0, "vuoto"
    hits, trovate = 0, []
    for voce in lex["words"] + lex["phrases"]:
        n = len(lingua.pattern_voce(voce["find"]).findall(text))
        if n:
            hits += n
            trovate.append(voce["find"])
    densita = hits * 100 / len(w)
    detail = f"{hits} cliché, {densita:.1f} ogni 100 parole"
    if trovate:
        detail += " (" + ", ".join(sorted(trovate)[:4]) + (", ..." if len(trovate) > 4 else "") + ")"
    return scala(densita, umano=0.0, macchina=4.0), detail


def ctrl_impronta(text, lang):
    """Caratteri che la tastiera di un telefono non produce da sola."""
    invisibili = sum(1 for c in text if unicodedata.category(c) == "Cf")
    lineette = text.count("—")
    curve = sum(text.count(c) for c in lingua.CURVE[lang])
    puntini = text.count("…")
    spazi = sum(text.count(c) for c in "   ")
    totale = invisibili * 4 + lineette * 2 + curve + puntini + spazi
    per1k = totale * 1000 / max(len(text), 1)
    return scala(per1k, umano=0.0, macchina=12.0), \
        (f"{invisibili} invisibili, {lineette} lineette lunghe, {curve} virgolette curve, "
         f"{puntini} puntini, {spazi} spazi rigidi")


def _strutture(text, lex):
    tells, nomi = 0, []
    for s in lex["structures"]:
        try:
            n = len(re.compile(s["regex"], re.MULTILINE).findall(text))
        except re.error:
            continue
        if n:
            tells += n
            nomi.append(s["id"])
    bullets = [len(b.split()) for b in re.findall(r"(?m)^\s*(?:[-*•]|✅|👉|➡️|🔹|✔️)\s+(.+)$", text)]
    uniformi = len(bullets) >= 3 and statistics.pstdev(bullets) < 1.6
    return tells, nomi, uniformi


def ctrl_voce(text, lex, lang):
    """Persona, registro parlato e le forme in cui i modelli ricadono."""
    w = lingua.parole(text)
    if len(w) < 25:
        return 50.0, "troppo corto per giudicare"
    per100 = 100 / len(w)
    tells, nomi, uniformi = _strutture(text, lex)
    if lang == "en":
        a = len(lingua.EN["contrazioni"].findall(text)) * per100
        b = len(lingua.EN["persona"].findall(text)) * per100
        score = (scala(a, umano=3.0, macchina=0.0) * 0.35
                 + scala(b, umano=8.0, macchina=1.0) * 0.35
                 + clamp(100 - tells * 22) * 0.30)
        detail = f"{a:.1f} contrazioni, {b:.1f} pronomi personali ogni 100 parole, {tells} strutture"
    else:
        a = len(lingua.IT["parlato"].findall(text)) * per100
        b = len(lingua.IT["persona"].findall(text)) * per100
        score = (scala(a, umano=1.5, macchina=0.0) * 0.25
                 + scala(b, umano=7.0, macchina=1.0) * 0.45
                 + clamp(100 - tells * 22) * 0.30)
        detail = f"{b:.1f} prima/seconda persona, {a:.1f} parlato ogni 100 parole, {tells} strutture"
    if uniformi:
        score -= 12
        nomi.append("elenco-uniforme")
    if nomi:
        detail += " [" + ", ".join(nomi[:4]) + "]"
    return clamp(score), detail


def esegui(text, lex, lang):
    r = {
        "RITMO": ctrl_ritmo(text, lang),
        "CONCRETEZZA": ctrl_concretezza(text, lang),
        "CLICHÉ": ctrl_cliche(text, lex),
        "IMPRONTA": ctrl_impronta(text, lang),
        "VOCE": ctrl_voce(text, lex, lang),
    }
    punteggi = [r[c][0] for c in CONTROLLI]
    # Il controllo più debole pesa: a un rilevatore basta un segnale.
    totale = statistics.mean(punteggi) * 0.6 + min(punteggi) * 0.4
    verdetto = "PASSA" if totale >= 70 and min(punteggi) >= 55 else (
        "RIVEDI" if totale >= 50 else "SEGNALATO")
    return r, totale, verdetto


def barra(score, width=24):
    pieni = round(score / 100 * width)
    return "#" * pieni + "." * (width - pieni)


def stampa(r, totale, verdetto, lang, etichetta=None, out=sys.stdout):
    t = f"PANNELLO RILEVAMENTO IA  [{lang}]" + (f"  -  {etichetta}" if etichetta else "")
    print("\n" + t, file=out)
    print("=" * max(len(t), 62), file=out)
    for nome in CONTROLLI:
        score, detail = r[nome]
        print(f"  {nome:<13} {barra(score)} {score:5.1f}", file=out)
        print(f"  {'':<13} {detail}", file=out)
    print("-" * 62, file=out)
    print(f"  {'UMANO':<13} {barra(totale)} {totale:5.1f}   {verdetto}", file=out)
    if verdetto != "PASSA":
        debole = min(CONTROLLI, key=lambda c: r[c][0])
        print(f"\n  Segnale più debole: {debole}. Parti da lì.", file=out)
    print("", file=out)


def main():
    ap = argparse.ArgumentParser(description="Stima quanto una bozza sembra scritta da una macchina.")
    ap.add_argument("input", nargs="?", default="-", help="file, oppure - per stdin")
    ap.add_argument("confronto", nargs="?", help="secondo file, per il prima/dopo")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--lingua", default="auto", choices=["auto", "it", "en"])
    ap.add_argument("--lessico", help="percorso di un lessico personalizzato")
    args = ap.parse_args()

    leggi = lambda p: sys.stdin.read() if p == "-" else open(p, encoding="utf-8").read()
    bersagli = [(args.input, leggi(args.input))]
    if args.confronto:
        bersagli.append((args.confronto, leggi(args.confronto)))

    payload = []
    for nome, text in bersagli:
        lang = lingua.scegli_lingua(text, args.lingua)
        lex = lingua.carica_lessico(lang, args.lessico)
        r, totale, verdetto = esegui(text, lex, lang)
        payload.append({
            "fonte": nome, "lingua": lang,
            "controlli": {k: {"punteggio": round(v[0], 1), "dettaglio": v[1]} for k, v in r.items()},
            "umano": round(totale, 1), "verdetto": verdetto,
            "_render": (r, totale, verdetto, lang),
        })

    if args.json:
        pulito = [{k: v for k, v in p.items() if k != "_render"} for p in payload]
        print(json.dumps(pulito if args.confronto else pulito[0], indent=2, ensure_ascii=False))
        return

    for (nome, _), p in zip(bersagli, payload):
        stampa(*p["_render"], etichetta=os.path.basename(nome) if args.confronto else None)
    if args.confronto:
        a, b = payload
        delta = b["umano"] - a["umano"]
        print(f"  {a['umano']:.1f} {a['verdetto']}  ->  {b['umano']:.1f} {b['verdetto']}   ({delta:+.1f})\n")

    sys.exit(0 if payload[-1]["verdetto"] == "PASSA" else 1)


if __name__ == "__main__":
    main()
