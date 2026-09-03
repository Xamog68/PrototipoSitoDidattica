#!/usr/bin/env python3

import json
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://unipi.coursecatalogue.cineca.it/api/v1"
OUTDIR = Path(__file__).resolve().parent

COORTE = 2026
CORSO_COD = "11514"

# Lista canonica LM 2026/27 ricavata dalla programmazione didattica ufficiale.
# campi: codice, semestre, titolo
CORSI = [
    ("089AA", "1", "Algebre e gruppi di Lie"),
    ("090AA", "1", "Analisi armonica"),
    ("699AA", "2", "Analisi dei dati"),
    ("798AA", "2", "Analisi superiore A"),
    ("096AA", "2", "Calcolo della variazioni A"),
    ("099AA", "1", "Complementi di analisi funzionale"),
    ("101AA", "2", "Determinazione orbitale"),
    ("553AA", "2", "Equazioni alle derivate parziali 2"),
    ("555AA", "2", "Equazioni differenziali stocastiche e applicazioni"),
    ("109AA", "2", "Equazioni ellittiche"),
    ("111AA", "2", "Fisica matematica"),
    ("0050A", "2", "Geometria algebrica complessa"),
    ("0019A", "1", "Geometria e analisi complessa"),
    ("130AA", "1", "Geometria riemanniana"),
    ("0020A", "1", "Introduzione alla statistica computazionale"),
    ("769AA", "1", "Istituzioni di algebra"),
    ("770AA", "1", "Istituzioni di analisi matematica"),
    ("772AA", "2", "Istituzioni di analisi numerica"),
    ("771AA", "1", "Istituzioni di didattica della matematica"),
    ("774AA", "1", "Istituzioni di fisica matematica"),
    ("768AA", "2", "Istituzioni di geometria"),
    ("773AA", "2", "Istituzioni di probabilità"),
    ("144AA", "2", "Meccanica spaziale"),
    ("145AA", "2", "Meccanica superiore"),
    ("775AA", "2", "Metodi di analisi armonica in analisi non lineare"),
    ("0058A", "2", "Metodi numerici per catene di Markov e reti complesse"),
    ("795AA", "1", "Metodi numerici per equazioni alle derivate parziali"),
    ("0056A", "2", "Metodi numerici per funzioni di matrici"),
    ("149AA", "1", "Metodi numerici per la grafica"),
    ("0057A", "1", "Modelli matematici e loro simulazione numerica"),
    ("559AA", "2", "Modelli matematici in biomedicina e fisica matematica"),
    ("166AA", "2", "Problem solving"),
    ("202AA", "2", "Teoria algebrica dei numeri 2"),
    ("706AA", "1", "Teoria algebrica dei numeri 3"),
    ("0065A", "1", "Teoria degli schemi"),
    ("211AA", "2", "Teoria dei giochi"),
    ("213AA", "2", "Teoria dei modelli"),
    ("224AA", "1", "Teoria ergodica"),
    ("225AA", "2", "Teoria geometrica della misura"),
    ("766AA", "2", "Topologia algebrica B"),
]


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def tutte_attivita(catalogo):
    out = []

    for corso in catalogo:
        for percorso in corso.get("percorsi", []):
            for anno in percorso.get("anni", []):

                for gruppo in anno.get("insegnamenti", []):
                    out.extend(gruppo.get("attivita", []))

                out.extend(anno.get("attivita", []))

    return out


def url_insegnamento(a):
    params = {
        "anno": a["aa"],
        "insegnamento": a["cod"],
        "ordinamento_aa": a["ordinamento_aa"],
        "af_percorso": a["corso_percorso_id"],
        "corso_cod": a["corso_cod"],
    }

    if a.get("schemaId") is not None:
        params["schema_id"] = a["schemaId"]

    return BASE + "/insegnamento?" + urllib.parse.urlencode(params)


print("Scarico il catalogo LM...")

catalog_url = f"{BASE}/corso/{COORTE}/{CORSO_COD}"
catalogo = get_json(catalog_url)

catalog_file = OUTDIR / f"catalogo_LM_{COORTE}_{CORSO_COD}.json"
catalog_file.write_text(
    json.dumps(catalogo, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

attivita = [
    a for a in tutte_attivita(catalogo)
    if str(a.get("aa")) == "2026"
]

indice = {}
for a in attivita:
    codice = a.get("adCod")
    if codice:
        indice.setdefault(codice, []).append(a)


def scegli_record(codice):
    candidati = indice.get(codice, [])

    if not candidati:
        return None

    # Quasi tutti i corsi compaiono in più percorsi.
    # Preferiamo un record con schemaId valorizzato e poi il percorso
    # con id numericamente più basso. Per il syllabus il contenuto
    # dell'attività è lo stesso.
    return sorted(
        candidati,
        key=lambda x: (
            x.get("schemaId") is None,
            int(x.get("corso_percorso_id") or 999999),
        )
    )[0]


risultato = []

print()
print("Scarico i syllabus LM...")

for codice, semestre, titolo in CORSI:
    print(f"{codice:5s}  {titolo}")

    record = scegli_record(codice)

    item = {
        "codice": codice,
        "cds": "LM",
        "anno_corso": "M",
        "semestre": semestre,
        "titolo_programmazione": titolo,
        "record_catalogo": record,
        "syllabus": None,
        "errore": None,
    }

    if record is None:
        item["errore"] = "Non trovato nel catalogo CINECA"
        risultato.append(item)
        continue

    try:
        url = url_insegnamento(record)
        item["url_api"] = url
        item["syllabus"] = get_json(url)
    except Exception as e:
        item["errore"] = str(e)

    risultato.append(item)


outfile = OUTDIR / "syllabus_lm_2026.json"
outfile.write_text(
    json.dumps(risultato, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

errori = [x for x in risultato if x["errore"]]

print()
print(f"Salvati {len(risultato)} insegnamenti in:")
print(outfile)
print(f"Errori di download: {len(errori)}")

if errori:
    print()
    print("Corsi con problemi:")
    for x in errori:
        print(
            f"  {x['codice']} {x['titolo_programmazione']}: "
            f"{x['errore']}"
        )
