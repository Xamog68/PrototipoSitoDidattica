#!/usr/bin/env python3

import json
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://unipi.coursecatalogue.cineca.it/api/v1"

OUTDIR = Path(__file__).resolve().parent
OUTDIR.mkdir(exist_ok=True)

CATALOGHI = [
    {"coorte": 2026, "anno_corso": 1, "corso_cod": "11515"},
    {"coorte": 2025, "anno_corso": 2, "corso_cod": "11515"},
    {"coorte": 2024, "anno_corso": 3, "corso_cod": "10299"},
]

# Lista canonica: programmazione didattica 2026/27
PROGRAMMAZIONE = [
    ("561AA", "I", "A", "Analisi matematica 1"),
    ("015AA", "I", "1", "Aritmetica"),
    ("241BB", "I", "2", "Fisica I con laboratorio"),
    ("017AA", "I", "1", "Fondamenti di programmazione con laboratorio"),
    ("614AA", "I", "A", "Geometria 1"),
    ("1993Z", "I", "A", "Laboratorio di introduzione alla matematica computazionale"),

    ("037AA", "II", "1", "Algebra 1"),
    ("039AA", "II", "2", "Algoritmi e strutture dati"),
    ("546AA", "II", "A", "Analisi matematica 2"),
    ("043AA", "II", "1", "Analisi numerica con laboratorio"),
    ("052AA", "II", "2", "Elementi di probabilità e statistica"),
    ("511AA", "II", "A", "Geometria 2"),

    ("038AA", "III", "2", "Algebra 2"),
    ("547AA", "III", "1", "Analisi matematica 3"),
    ("044AA", "III", "1", "Calcolo scientifico"),
    ("046AA", "III", "2", "Elementi di analisi complessa"),
    ("047AA", "III", "1", "Elementi di calcolo delle variazioni"),
    ("049AA", "III", "1", "Elementi di geometria algebrica"),
    ("051AA", "III", "2", "Elementi di meccanica celeste"),
    ("053AA", "III", "2", "Elementi di teoria degli insiemi"),
    ("054AA", "III", "1", "Elementi di topologia algebrica"),
    ("545AA", "III", "2", "Equazioni alle derivate parziali"),
    ("242BB", "III", "1", "Fisica II"),
    ("243BB", "III", "2", "Fisica III"),
    ("055AA", "III", "1", "Geometria e topologia differenziale"),
    ("058AA", "III", "A", "Laboratorio computazionale"),
    ("062AA", "III", "2", "Laboratorio sperimentale di matematica computazionale"),
    ("063AA", "III", "1", "Linguaggi di programmazione con laboratorio"),
    ("064AA", "III", "2", "Logica matematica"),
    ("065AA", "III", "1", "Matematiche elementari da un punto di vista superiore: aritmetica"),
    ("575AA", "III", "2", "Meccanica razionale"),
    ("067AA", "III", "2", "Metodi numerici per equazioni differenziali ordinarie"),
    ("0047A", "III", "1", "Ottimizzazione non lineare"),
    ("070AA", "III", "1", "Probabilità"),
    ("072AA", "III", "2", "Ricerca operativa"),
    ("074AA", "III", "1", "Sistemi dinamici"),
    ("075AA", "III", "2", "Statistica matematica"),
    ("219AA", "III", "1", "Teoria della misura"),
]


def get_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(req) as response:
        return json.load(response)


def tutte_attivita(catalogo):
    risultato = []

    for corso in catalogo:
        for percorso in corso.get("percorsi", []):
            for anno in percorso.get("anni", []):

                for gruppo in anno.get("insegnamenti", []):
                    risultato.extend(gruppo.get("attivita", []))

                risultato.extend(anno.get("attivita", []))

    return risultato


print("Scarico i cataloghi CINECA...")

attivita = []

for cat in CATALOGHI:
    url = f"{BASE}/corso/{cat['coorte']}/{cat['corso_cod']}"
    print(" ", url)

    dati = get_json(url)

    # Conserviamo anche una copia grezza del catalogo
    rawfile = OUTDIR / f"catalogo_{cat['coorte']}_{cat['corso_cod']}.json"
    rawfile.write_text(
        json.dumps(dati, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    for a in tutte_attivita(dati):
        if str(a.get("aa")) == "2026":
            a["_coorte_origine"] = cat["coorte"]
            attivita.append(a)


# indicizza tutte le occorrenze per codice AD
indice = {}

for a in attivita:
    codice = a.get("adCod")
    if codice:
        indice.setdefault(codice, []).append(a)


def scegli_record(codice):
    candidati = indice.get(codice, [])

    if not candidati:
        return None

    # Preferiamo record con schemaId valorizzato.
    # Se non ce ne sono, va bene anche schemaId=null:
    # l'endpoint funziona omettendo schema_id.
    candidati = sorted(
        candidati,
        key=lambda x: (
            x.get("schemaId") is None,
            x.get("_coorte_origine", 9999)
        )
    )

    return candidati[0]


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


risultato = []

print()
print("Scarico i syllabus...")

for codice, anno, semestre, titolo_programmazione in PROGRAMMAZIONE:

    print(f"{codice:5s}  {titolo_programmazione}")

    record = scegli_record(codice)

    item = {
        "codice": codice,
        "anno_corso": anno,
        "semestre": semestre,
        "titolo_programmazione": titolo_programmazione,
        "record_catalogo": record,
        "syllabus": None,
        "errore": None,
    }

    if record is None:
        item["errore"] = "Non trovato nei cataloghi CINECA"
        risultato.append(item)
        continue

    try:
        url = url_insegnamento(record)
        syllabus = get_json(url)

        item["url_api"] = url
        item["syllabus"] = syllabus

    except Exception as e:
        item["errore"] = str(e)

    risultato.append(item)


outfile = OUTDIR / "syllabus_2026.json"

outfile.write_text(
    json.dumps(risultato, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print()
print(f"Salvati {len(risultato)} insegnamenti in:")
print(outfile)
