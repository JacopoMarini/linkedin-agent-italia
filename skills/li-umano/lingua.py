"""
lingua.py - tutto quello che negli script dipende dalla lingua.

Gli script originali erano scritti per l'inglese: contavano le contrazioni
("don't", "it's"), tokenizzavano solo lettere ASCII e cercavano cliché
inglesi. In italiano tutte e tre le cose falliscono in silenzio. Qui stanno
le regole per lingua, cosi umanizza.py e rileva.py restano uguali per tutte.

Lingue supportate: "it" (predefinita) e "en".
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

LESSICI = {
    "it": os.path.join(HERE, "lessico.it.json"),
    "en": os.path.join(HERE, "lessico.en.json"),
}

# Parole funzionali molto frequenti: bastano per capire la lingua di un post.
_STOP = {
    "it": set("""il lo la i gli le un una uno di da in con su per tra fra che non
        è e ma se come anche più ho hai ha abbiamo sono sei siamo questo questa
        quello quella del della dei delle nel nella al alla mi ti ci si perché
        quando cosa poi già ancora molto tutto tutti""".split()),
    "en": set("""the a an of to in on for with that this is are was were be been
        and but if as at by from it its i you we they my your our not do does did
        have has had what when why how all more very just""".split()),
}

WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)
SENT_RE = re.compile(r"[^.!?\n]+[.!?]*")


def rileva_lingua(text):
    """'it' o 'en' contando le parole funzionali. In caso di dubbio: 'it'."""
    parole = [w.lower().replace("’", "'") for w in WORD_RE.findall(text)]
    # In italiano l'elisione unisce articolo e nome: "l'intelligenza" -> "l", "intelligenza".
    piatte = []
    for w in parole:
        piatte.extend(p for p in w.split("'") if p)
    conta = {lang: sum(1 for w in piatte if w in stop) for lang, stop in _STOP.items()}
    if conta["en"] > conta["it"] * 1.3 and conta["en"] >= 3:
        return "en"
    return "it"


def scegli_lingua(text, richiesta="auto"):
    return rileva_lingua(text) if richiesta in (None, "", "auto") else richiesta


def carica_lessico(lang, percorso=None):
    with open(percorso or LESSICI[lang], encoding="utf-8") as fh:
        return json.load(fh)


def parole(text):
    return WORD_RE.findall(text)


def frasi(text):
    return [s.strip() for s in SENT_RE.findall(text) if len(s.split()) > 2]


def pattern_voce(find):
    """Regex per una voce del lessico: confini di parola Unicode, spazi elastici,
    apostrofo dritto o tipografico indifferente."""
    esc = re.escape(find).replace(r"\ ", r"\s+")
    esc = esc.replace("'", "['’]").replace(r"\'", "['’]")
    return re.compile(r"(?<![^\W_])" + esc + r"(?![^\W_])", re.IGNORECASE)


# --- segnali di VOCE -------------------------------------------------------

# Inglese: come l'originale. Le contrazioni sono il segnale più forte di
# scrittura parlata, e i modelli le evitano.
EN = {
    "contrazioni": re.compile(r"\b\w+'(?:s|t|re|ve|ll|d|m)\b", re.IGNORECASE),
    "persona": re.compile(r"\b(i|me|my|mine|we|us|our|you|your)\b", re.IGNORECASE),
}

# Italiano: le contrazioni non esistono e il soggetto si omette ("ho fatto",
# non "io ho fatto"), quindi contare i pronomi non basta. Si contano le forme
# di prima e seconda persona più comuni, e i segnali di registro parlato che
# i modelli quasi non usano.
IT = {
    "persona": re.compile(r"""(?<![^\W_])(?:
        io|me|mi|mio|mia|miei|mie|noi|ci|ce|nostro|nostra|nostri|nostre|
        tu|te|ti|tuo|tua|tuoi|tue|voi|vi|vostro|vostra|vostri|vostre|
        ho|hai|abbiamo|avete|sei|siamo|siete|sono\s+stat[oaie]|
        faccio|fai|facciamo|fate|posso|puoi|possiamo|voglio|vuoi|vogliamo|
        devo|devi|dobbiamo|so|sai|sappiamo|penso|pensi|credo|dico|dici|
        scrivo|usavo|ricordo|ammetto|confesso|sbagliavo|pensavo|volevo
        )(?![^\W_])""", re.IGNORECASE | re.VERBOSE),
    "parlato": re.compile(r"""(?<![^\W_])(?:
        tipo|insomma|cioè|beh|boh|mah|ok|okay|dai|figurati|magari|
        comunque|tra\s+l['’]altro|un\s+sacco|roba|alla\s+fine|onestamente|
        sinceramente|tipo\s+che|praticamente|a\s+dire\s+il\s+vero|
        mica|pure|eh|vabbè|niente|zero
        )(?![^\W_])""", re.IGNORECASE | re.VERBOSE),
}

# --- segnali di SPECIFICITÀ ------------------------------------------------

NUMERI = {
    # 1.200 / 3,5% / € 40 / 40€ / 2026 / 15 min
    "it": re.compile(r"(?<![\w.,])\d[\d.,]*\s?%?|€\s?\d|\d\s?€"),
    "en": re.compile(r"\b\d[\d,.]*%?\b|\$\d"),
}
# In italiano i numeri si scrivono spesso in lettere ("tre ore") e i post
# tecnici sono pieni di sigle (CI, API, UTC, PR). Giorni e mesi sono ancore
# concrete. Tutti contano come dettaglio. ("sei" escluso: è anche "tu sei".)
CONCRETI_IT = re.compile(r"""(?<![^\W_])(?:
    due|tre|quattro|cinque|sette|otto|nove|dieci|undici|dodici|quindici|venti|
    trenta|quaranta|cinquanta|cento|duecento|mille|mezz['’]ora|
    lunedì|martedì|mercoledì|giovedì|venerdì|sabato|domenica|
    gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|
    ottobre|novembre|dicembre
    )(?![^\W_])|(?<![^\W_])(?-i:[A-Z]{2,6})(?![^\W_])""", re.IGNORECASE | re.VERBOSE)

# Nome proprio: maiuscola non a inizio frase. Lettere accentate incluse.
PROPRI = re.compile(r"(?<![.!?]\s)(?<!^)(?<![^\W_])[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]{2,}",
                    re.MULTILINE)

# --- impronta tipografica --------------------------------------------------

# In italiano l'apostrofo tipografico (’) è quello che iPhone e Mac
# inseriscono da soli in "l’IA", "dell’anno": penalizzarlo colpirebbe chi
# scrive a mano. Le virgolette basse «» sono italiano corretto. Si contano solo
# i segni che una tastiera non produce da sola.
CURVE = {"it": "“”", "en": "‘’“”"}

# Connettivi da promuovere a inizio frase quando una lineetta diventata
# virgola lascia una frase spezzata male.
CONNETTIVI = {
    "it": r"anche|quindi|comunque|alla fine|eppure|poi",
    "en": r"also|so|still|basically|in the end",
}
