#!/usr/bin/env python3

import json
import html
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent
INPUT = BASE / "syllabus_2026.json"
OUTPUT = BASE.parent / "docs" / "index.html"


# ------------------------------------------------------------
# Utility
# ------------------------------------------------------------

def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def strip_html(value):
    """Versione testuale, usata solo per conteggi/diagnostica."""
    value = clean(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def get_testo(syllabus, key):
    testi = syllabus.get("testiTotali") or []
    if not testi:
        return ""
    return clean(testi[0].get(key))


def get_altri_testi(syllabus):
    """
    Gli 'altri testi' CINECA sono dentro testiTotali[0].
    Ogni voce contiene:
      etichetta_it / etichetta_en
      altri_testi_it / altri_testi_en
    """
    result = {}

    testi = syllabus.get("testiTotali") or []
    if not testi:
        return result

    for x in testi[0].get("altri_testi", []) or []:
        label = clean(x.get("etichetta_it"))
        value = clean(x.get("altri_testi_it"))

        if label:
            result[label.lower()] = value

    return result


def normalize_label(value):
    return (
        value.lower()
        .replace("à", "a")
        .replace("è", "e")
        .replace("é", "e")
        .replace("ì", "i")
        .replace("ò", "o")
        .replace("ù", "u")
    )


def find_extra(extra, *needles):
    needles = [normalize_label(x) for x in needles]

    for key, value in extra.items():
        normalized = normalize_label(key)
        for needle in needles:
            if needle in normalized:
                return value

    return ""


def teachers(syllabus):
    names = []

    for d in syllabus.get("docenti", []) or []:
        name = clean(d.get("des"))
        if name and name not in names:
            names.append(name)

    return ", ".join(names)


def button(label, panel_id, value, secondary=False):
    classes = "field-button present"
    if secondary:
        classes += " secondary"

    if value:
        return (
            f'<button class="{classes}" '
            f'onclick="openPanel(\'{panel_id}\', this)">'
            f'{html.escape(label)}</button>'
        )

    # I campi principali mancanti sono informativi.
    if not secondary:
        return (
            f'<button class="field-button absent" disabled>'
            f'{html.escape(label)} ✕</button>'
        )

    # I campi secondari mancanti non vengono mostrati.
    return ""


# ------------------------------------------------------------
# Lettura dataset
# ------------------------------------------------------------

with INPUT.open(encoding="utf-8") as f:
    data = json.load(f)


courses_html = []

count_missing_program = 0
count_short = 0
count_ok = 0


for n, item in enumerate(data):

    syllabus = item.get("syllabus") or {}
    record = item.get("record_catalogo") or {}

    code = clean(item.get("codice"))
    year = clean(item.get("anno_corso"))
    semester = clean(item.get("semestre"))

    title = (
        clean(syllabus.get("des_it"))
        or clean(item.get("titolo_programmazione"))
    )

    docente = teachers(syllabus) or "—"

    programma_it = get_testo(syllabus, "contenuti_it")
    programma_en = get_testo(syllabus, "contenuti_en")

    obiettivi_it = get_testo(syllabus, "obiettivi_formativi_it")
    obiettivi_en = get_testo(syllabus, "obiettivi_formativi_en")

    prerequisiti_it = get_testo(syllabus, "prerequisiti_it")
    prerequisiti_en = get_testo(syllabus, "prerequisiti_en")

    extra = get_altri_testi(syllabus)

    esame = (
        find_extra(extra, "modalita d'esame")
        or find_extra(extra, "modalita di esame")
        or find_extra(extra, "esame")
    )

    bibliografia = (
        find_extra(extra, "bibliografia")
        or find_extra(extra, "materiale didattico")
    )

    capacita = find_extra(extra, "capacita")

    metodi = (
        find_extra(extra, "indicazioni metodologiche")
        or get_testo(syllabus, "metodi_didattici_est_it")
        or clean(syllabus.get("metodi_didattici_it"))
    )

    verifica = (
        get_testo(syllabus, "verifica_apprendimento_it")
        or find_extra(extra, "modalita di verifica delle conoscenze")
    )

    comportamenti = find_extra(
        extra,
        "modalita di verifica dei comportamenti"
    )

    non_frequentanti = find_extra(
        extra,
        "indicazioni per non frequentanti"
    )

    prereq_successivi = find_extra(
        extra,
        "prerequisiti per studi successivi"
    )

    pagina_web = find_extra(
        extra,
        "pagina web del corso"
    )

    altri_link = find_extra(
        extra,
        "altri riferimenti web"
    )

    stage = find_extra(
        extra,
        "stage e tirocini"
    )

    # --------------------------------------------------------
    # Diagnostica
    # --------------------------------------------------------

    chars = len(strip_html(programma_it))

    if not programma_it:
        status = "missing"
        status_label = "Syllabus mancante"
        count_missing_program += 1

    elif chars < 300:
        status = "very-short"
        status_label = f"Programma molto breve · {chars} caratteri"
        count_short += 1

    elif chars < 600:
        status = "short"
        status_label = f"Programma breve · {chars} caratteri"
        count_short += 1

    else:
        status = "ok"
        status_label = f"Programma presente · {chars} caratteri"
        count_ok += 1

    # --------------------------------------------------------
    # URL umana del Course Catalogue
    # --------------------------------------------------------

    aa = record.get("aa")
    cod = record.get("cod")
    ordinamento = record.get("ordinamento_aa")
    corso_cod = record.get("corso_cod")
    percorso = record.get("corso_percorso_id")
    schema = record.get("schemaId")

    cineca_url = ""

    if aa and cod and ordinamento and corso_cod and percorso:
        cineca_url = (
            f"https://unipi.coursecatalogue.cineca.it/"
            f"corsi/{ordinamento}/{corso_cod}/"
            f"insegnamenti/{aa}/{cod}/"
            f"{ordinamento}/{percorso}"
        )

        if schema:
            cineca_url += f"?schemaid={schema}"

    cineca_button = ""

    if cineca_url:
        cineca_button = (
            f'<a class="cineca-button" '
            f'href="{html.escape(cineca_url)}" '
            f'target="_blank" rel="noopener">'
            f'CINECA ↗</a>'
        )

    # --------------------------------------------------------
    # Campi principali e secondari
    # --------------------------------------------------------

    primary_fields = [
        ("Programma", programma_it),
        ("Obiettivi", obiettivi_it),
        ("Prerequisiti", prerequisiti_it),
        ("Esame", esame),
        ("Bibliografia", bibliografia),
    ]

    secondary_fields = [
        ("Capacità", capacita),
        ("Metodi didattici", metodi),
        ("Verifica apprendimento", verifica),
        ("Verifica comportamenti", comportamenti),
        ("Non frequentanti", non_frequentanti),
        ("Prerequisiti successivi", prereq_successivi),
        ("Pagina web", pagina_web),
        ("Altri link", altri_link),
        ("Stage", stage),
        ("Programma EN", programma_en),
        ("Obiettivi EN", obiettivi_en),
        ("Prerequisiti EN", prerequisiti_en),
    ]

    all_fields = primary_fields + secondary_fields

    primary_buttons = []
    secondary_buttons = []
    panels = []

    for k, (label, value) in enumerate(all_fields):

        panel_id = f"panel_{n}_{k}"
        is_secondary = k >= len(primary_fields)

        b = button(label, panel_id, value, secondary=is_secondary)

        if is_secondary:
            if b:
                secondary_buttons.append(b)
        else:
            primary_buttons.append(b)

        if value:
            panels.append(
                f"""
                <section class="detail-panel" id="{panel_id}">
                    <div class="detail-header">
                        <strong>{html.escape(label)}</strong>
                        <button class="close-button"
                                onclick="closePanel('{panel_id}')">
                            Chiudi
                        </button>
                    </div>
                    <div class="detail-content">
                        {value}
                    </div>
                </section>
                """
            )

    search_string = " ".join(
        [code, title, docente, year, semester]
    ).lower()

    missing_primary = sum(
        1 for _, value in primary_fields if not value
    )

    secondary_block = ""

    if secondary_buttons:
        secondary_block = f"""
        <div class="secondary-actions">
            {" ".join(secondary_buttons)}
        </div>
        """

    courses_html.append(
        f"""
        <article class="course {status}"
                 data-year="{html.escape(year)}"
                 data-semester="{html.escape(semester)}"
                 data-status="{status}"
                 data-search="{html.escape(search_string)}"
                 data-missing="{missing_primary}">

            <div class="course-row">

                <div class="metadata">
                    <span class="year-badge">{html.escape(year)}</span>
                    <span class="semester-badge">{html.escape(semester)}</span>
                </div>

                <div class="identity">
                    <div class="course-code">{html.escape(code)}</div>
                    <div class="course-title">{html.escape(title)}</div>
                    <div class="course-teachers">{html.escape(docente)}</div>
                </div>

                <div class="status-column">
                    <span class="status-badge {status}">
                        {html.escape(status_label)}
                    </span>
                </div>

                <div class="course-actions">

                    <div class="primary-actions">
                        {" ".join(primary_buttons)}
                        {cineca_button}
                    </div>

                    {secondary_block}

                </div>

            </div>

            <div class="details">
                {"".join(panels)}
            </div>

        </article>
        """
    )


# ------------------------------------------------------------
# HTML finale
# ------------------------------------------------------------

page = f"""<!doctype html>
<html lang="it">

<head>

<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">

<title>Syllabus — CdS in Matematica</title>

<style>

:root {{
    --blue: #17365d;
    --border: #d9dee5;
    --background: #f5f6f8;
    --text: #20242a;
    --muted: #66717f;
    --danger: #b42318;
    --danger-bg: #fff1f0;
    --warning: #8a5a00;
    --warning-bg: #fff8e6;
    --ok: #216e39;
    --ok-bg: #edf7ef;
}}

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family:
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    background: var(--background);
    color: var(--text);
}}

header {{
    background: var(--blue);
    color: white;
    padding: 28px 32px 24px;
}}

.header-inner {{
    max-width: 1700px;
    margin: auto;
}}

h1 {{
    margin: 0 0 6px;
    font-size: 30px;
    line-height: 1.15;
}}

.subtitle {{
    opacity: .82;
    font-size: 15px;
}}

.summary {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-top: 22px;
}}

.summary-card {{
    background: rgba(255,255,255,.12);
    border: 1px solid rgba(255,255,255,.17);
    border-radius: 9px;
    padding: 9px 14px;
}}

.summary-number {{
    display: block;
    font-size: 21px;
    font-weight: 750;
}}

.summary-label {{
    font-size: 12px;
    opacity: .85;
}}

.toolbar {{
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(255,255,255,.96);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--border);
    padding: 12px 24px;
}}

.toolbar-inner {{
    max-width: 1700px;
    margin: auto;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}}

.search {{
    flex: 1 1 280px;
    min-width: 220px;
    max-width: 430px;
    border: 1px solid #b9c1cb;
    border-radius: 7px;
    padding: 8px 11px;
    font-size: 14px;
}}

.filter-button {{
    border: 1px solid #bcc4ce;
    border-radius: 7px;
    padding: 7px 11px;
    background: white;
    cursor: pointer;
}}

.filter-button:hover {{
    background: #f1f3f5;
}}

.filter-button.active {{
    background: var(--blue);
    color: white;
    border-color: var(--blue);
}}

.result-count {{
    margin-left: auto;
    font-size: 13px;
    color: var(--muted);
}}

main {{
    max-width: 1700px;
    margin: auto;
    padding: 20px 24px 60px;
}}

.course {{
    background: white;
    border: 1px solid var(--border);
    border-left: 5px solid #6688a7;
    border-radius: 8px;
    margin-bottom: 9px;
    overflow: hidden;
}}

.course.missing {{
    border-left-color: var(--danger);
}}

.course.short,
.course.very-short {{
    border-left-color: #c78913;
}}

.course-row {{
    display: grid;
    grid-template-columns:
        85px
        minmax(290px, 1.5fr)
        minmax(180px, .65fr)
        minmax(450px, 2fr);
    gap: 14px;
    align-items: center;
    padding: 13px 15px;
}}

.metadata {{
    display: flex;
    gap: 5px;
}}

.year-badge,
.semester-badge {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 33px;
    height: 27px;
    border-radius: 5px;
    font-size: 12px;
    font-weight: 700;
}}

.year-badge {{
    background: #e6edf5;
    color: #264d73;
}}

.semester-badge {{
    background: #ececec;
    color: #444;
}}

.course-code {{
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 2px;
}}

.course-title {{
    font-weight: 720;
    line-height: 1.25;
}}

.course-teachers {{
    font-size: 13px;
    color: var(--muted);
    margin-top: 4px;
}}

.status-badge {{
    display: inline-block;
    font-size: 11px;
    font-weight: 650;
    padding: 5px 8px;
    border-radius: 5px;
}}

.status-badge.ok {{
    color: var(--ok);
    background: var(--ok-bg);
}}

.status-badge.missing {{
    color: var(--danger);
    background: var(--danger-bg);
}}

.status-badge.short,
.status-badge.very-short {{
    color: var(--warning);
    background: var(--warning-bg);
}}

.course-actions {{
    display: block;
}}

.primary-actions,
.secondary-actions {{
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
}}

.secondary-actions {{
    margin-top: 7px;
    padding-top: 7px;
    border-top: 1px dotted #d5d9de;
    opacity: .80;
}}

.field-button,
.cineca-button,
.close-button {{
    font: inherit;
}}

.field-button {{
    border: 1px solid #b7c0ca;
    border-radius: 5px;
    padding: 5px 8px;
    font-size: 11px;
    background: #fafbfc;
    cursor: pointer;
}}

.secondary-actions .field-button {{
    font-size: 10px;
    padding: 4px 7px;
}}

.field-button.present:hover {{
    background: #e9eff5;
    border-color: #8297aa;
}}

.field-button.present.active {{
    background: var(--blue);
    color: white;
    border-color: var(--blue);
}}

.field-button.absent {{
    color: #aa4b45;
    background: #fff7f7;
    border-color: #e3c7c5;
    cursor: default;
}}

.cineca-button {{
    display: inline-flex;
    align-items: center;
    padding: 5px 8px;
    border: 1px solid #72849a;
    border-radius: 5px;
    background: #f1f5f8;
    color: #274966;
    text-decoration: none;
    font-size: 11px;
    font-weight: 650;
}}

.cineca-button:hover {{
    background: #dfe9f1;
}}

.detail-panel {{
    display: none;
    border-top: 1px solid var(--border);
    background: #fbfbfc;
    padding: 18px 24px 22px;
}}

.detail-panel.open {{
    display: block;
}}

.detail-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}}

.close-button {{
    border: 0;
    background: transparent;
    color: var(--muted);
    cursor: pointer;
}}

.close-button:hover {{
    text-decoration: underline;
}}

.detail-content {{
    max-width: 1050px;
    line-height: 1.55;
    font-size: 14px;
}}

.detail-content p:first-child {{
    margin-top: 0;
}}

.detail-content a {{
    overflow-wrap: anywhere;
}}

.hidden {{
    display: none;
}}

.no-results {{
    display: none;
    text-align: center;
    padding: 60px 20px;
    color: var(--muted);
}}

footer {{
    max-width: 1700px;
    margin: auto;
    padding: 0 24px 40px;
    color: var(--muted);
    font-size: 12px;
}}

@media (max-width: 1150px) {{

    .course-row {{
        grid-template-columns: 80px 1fr;
    }}

    .status-column,
    .course-actions {{
        grid-column: 2;
    }}

}}

@media (max-width: 650px) {{

    header {{
        padding: 22px 18px;
    }}

    .toolbar {{
        padding: 10px 12px;
    }}

    main {{
        padding: 14px 10px 50px;
    }}

    .course-row {{
        display: block;
    }}

    .metadata,
    .identity,
    .status-column,
    .course-actions {{
        margin-bottom: 10px;
    }}

}}

</style>

<script>

let yearFilter = "ALL";
let semesterFilter = "ALL";
let missingOnly = false;


function openPanel(id, button) {{

    const course = button.closest(".course");

    course.querySelectorAll(".detail-panel").forEach(panel => {{
        if (panel.id !== id) {{
            panel.classList.remove("open");
        }}
    }});

    course.querySelectorAll(".field-button").forEach(b => {{
        if (b !== button) {{
            b.classList.remove("active");
        }}
    }});

    const panel = document.getElementById(id);
    const opening = !panel.classList.contains("open");

    panel.classList.toggle("open", opening);
    button.classList.toggle("active", opening);
}}


function closePanel(id) {{

    const panel = document.getElementById(id);
    panel.classList.remove("open");

    const course = panel.closest(".course");

    course.querySelectorAll(".field-button").forEach(b => {{
        b.classList.remove("active");
    }});
}}


function setYear(year, button) {{

    yearFilter = year;

    document.querySelectorAll("[data-year-filter]").forEach(b => {{
        b.classList.remove("active");
    }});

    button.classList.add("active");

    applyFilters();
}}


function setSemester(semester, button) {{

    semesterFilter = semester;

    document.querySelectorAll("[data-semester-filter]").forEach(b => {{
        b.classList.remove("active");
    }});

    button.classList.add("active");

    applyFilters();
}}


function toggleMissing(button) {{

    missingOnly = !missingOnly;
    button.classList.toggle("active", missingOnly);

    applyFilters();
}}


function applyFilters() {{

    const query =
        document.getElementById("search")
        .value
        .trim()
        .toLowerCase();

    let visible = 0;

    document.querySelectorAll(".course").forEach(course => {{

        const yearOK =
            yearFilter === "ALL" ||
            course.dataset.year === yearFilter;

        const semesterOK =
            semesterFilter === "ALL" ||
            course.dataset.semester === semesterFilter;

        const missingOK =
            !missingOnly ||
            course.dataset.status === "missing";

        const searchOK =
            !query ||
            course.dataset.search.includes(query);

        const show =
            yearOK &&
            semesterOK &&
            missingOK &&
            searchOK;

        course.classList.toggle("hidden", !show);

        if (show) visible++;
    }});

    document.getElementById("result-count").textContent =
        visible + " insegnamenti";

    document.getElementById("no-results").style.display =
        visible === 0 ? "block" : "none";
}}


function resetFilters() {{

    yearFilter = "ALL";
    semesterFilter = "ALL";
    missingOnly = false;

    document.getElementById("search").value = "";

    document.querySelectorAll(".filter-button").forEach(b => {{
        b.classList.remove("active");
    }});

    document.querySelector(
        '[data-year-filter="ALL"]'
    ).classList.add("active");

    document.querySelector(
        '[data-semester-filter="ALL"]'
    ).classList.add("active");

    applyFilters();
}}

</script>

</head>

<body>

<header>

<div class="header-inner">

    <h1>Syllabus — CdS in Matematica</h1>

    <div class="subtitle">
        Anno accademico 2026/27 · quadro degli insegnamenti attivati
    </div>

    <div class="summary">

        <div class="summary-card">
            <span class="summary-number">{len(data)}</span>
            <span class="summary-label">insegnamenti</span>
        </div>

        <div class="summary-card">
            <span class="summary-number">{count_missing_program}</span>
            <span class="summary-label">programmi mancanti</span>
        </div>

        <div class="summary-card">
            <span class="summary-number">{count_short}</span>
            <span class="summary-label">programmi brevi</span>
        </div>

    </div>

</div>

</header>


<div class="toolbar">

<div class="toolbar-inner">

    <input
        id="search"
        class="search"
        type="search"
        placeholder="Cerca corso, codice o docente…"
        oninput="applyFilters()"
    >

    <button
        class="filter-button active"
        data-year-filter="ALL"
        onclick="setYear('ALL', this)">
        Tutti
    </button>

    <button
        class="filter-button"
        data-year-filter="I"
        onclick="setYear('I', this)">
        I
    </button>

    <button
        class="filter-button"
        data-year-filter="II"
        onclick="setYear('II', this)">
        II
    </button>

    <button
        class="filter-button"
        data-year-filter="III"
        onclick="setYear('III', this)">
        III
    </button>

    <span style="width:8px"></span>

    <button
        class="filter-button active"
        data-semester-filter="ALL"
        onclick="setSemester('ALL', this)">
        Sem. tutti
    </button>

    <button
        class="filter-button"
        data-semester-filter="1"
        onclick="setSemester('1', this)">
        Sem. 1
    </button>

    <button
        class="filter-button"
        data-semester-filter="2"
        onclick="setSemester('2', this)">
        Sem. 2
    </button>

    <button
        class="filter-button"
        data-semester-filter="A"
        onclick="setSemester('A', this)">
        Annuali
    </button>

    <button
        class="filter-button"
        onclick="toggleMissing(this)">
        Solo mancanti
    </button>

    <button
        class="filter-button"
        onclick="resetFilters()">
        Reset
    </button>

    <div
        id="result-count"
        class="result-count">
        {len(data)} insegnamenti
    </div>

</div>

</div>


<main>

{"".join(courses_html)}

<div id="no-results" class="no-results">
    Nessun insegnamento corrisponde ai filtri.
</div>

</main>


<footer>
    Dati estratti dal Course Catalogue dell'Università di Pisa.
    Pagina generata automaticamente.
</footer>

</body>

</html>
"""


OUTPUT.write_text(page, encoding="utf-8")

print()
print("Pagina generata:")
print(OUTPUT)
print()
print(f"Insegnamenti: {len(data)}")
print(f"Programmi mancanti: {count_missing_program}")
print(f"Programmi brevi: {count_short}")
