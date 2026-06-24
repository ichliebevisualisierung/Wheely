# Autonomous Rover — Project Blueprint

**Project:** AI-gestützter autonomer Rover (Freenove Tank Robot + LLM-Agent)
**Zeitrahmen:** 3 Wochen
**Team:** Gruppenarbeit, Python-Einsteiger mit starkem Java-Hintergrund
**Hardware:** Freenove Tank Robot Kit, Raspberry Pi Zero 2 W, Laptop als Rechen-Einheit

---

## 1. Zielbild (was am Ende funktionieren soll)

Der Rover bekommt über einen **Text-Chat** (Terminal/VS Code) Befehle wie *"finde die Flasche"* und setzt sie selbstständig um. Dafür:

1. **Erkundet** er einen unbekannten Raum (Erkundungsfahrt).
2. Baut sich dabei ein **mentales Modell** des Raums (eine Karte aus Orten + Verbindungen).
3. **Erkennt Objekte** über die Kamera (eine Handvoll Alltagsgegenstände).
4. **Findet kürzeste Wege** zu bekannten Orten in dieser Karte.
5. **Interpretiert spontane Befehle** und übersetzt sie in Fahr-/Greif-Aktionen.

**Bewusst außerhalb des Scope (für später offengehalten):**
- Plant-Health-Analyse (späteres optionales Wahrnehmungs-Modul)
- Sprachsteuerung (Mikrofon) — Text-Chat reicht
- Zentimetergenaue geometrische Karte (echtes SLAM)

---

## 2. Grundsatz-Entscheidungen (das Fundament)

### 2.1 Verteilte Architektur: Pi = Körper, Laptop = Gehirn

Der Pi Zero 2 W ist zu schwach, um KI lokal zu rechnen — muss er auch nicht.

| | Läuft auf | Aufgabe |
|---|---|---|
| **Körper** | Raspberry Pi | Motoren, Servos, Sensoren lesen, Kamera streamen |
| **Gehirn** | Laptop | Objekterkennung, LLM-Agent, Kartenlogik, Chat |

Kommunikation: Pi und Laptop reden über WLAN (TCP-Sockets, wie in Freenoves Client/Server schon angelegt).

**Warum so?** Der Laptop ist stark, hat Internet für die LLM-API und ist bequem zum Entwickeln. Der Pi macht nur das, wofür er da ist: Hardware bewegen. Diese Trennung ist auch ideal für Gruppenarbeit — Körper-Team und Gehirn-Team blockieren sich nicht.

### 2.2 "YOLO sieht, LLM denkt" — Wahrnehmung und Denken getrennt

Eure kostenlosen Uni-LLMs sind Text-Modelle. Sie können kein Bild "sehen". Also trennen wir die Aufgaben:

- **YOLO** (lokales Objekterkennungs-Modell, kostenlos, läuft auf dem Laptop) ist das **Auge**. Es wandelt ein Kamerabild in eine *Textbeschreibung*: "Flasche bei x=320, Stuhl bei x=80".
- **Das LLM** (euer Uni-Modell) ist der **Verstand**. Es bekommt diese Textbeschreibung + das Ziel + die Karte und entscheidet die nächste Aktion.

Das ist robuster, schneller und kostenlos im Dauerbetrieb. Wichtig: Es ist auch die saubere Lösung, um später ein Vision-LLM anzudocken (siehe 2.3).

### 2.3 Offene Schnittstelle für später (komplexere KI)

Wir definieren die Wahrnehmung als **austauschbares Modul** mit fester Schnittstelle:

```
perceive(image) -> Liste[ erkanntes Objekt {label, position, confidence} ]
```

Heute steckt dahinter YOLO. Später kann dahinter ein Vision-LLM (Claude/GPT-4o) stecken, ohne dass der Rest des Codes sich ändert. Genau dieselbe Idee für das Denk-Modul:

```
decide(ziel, wahrnehmung, karte) -> naechste_aktion
```

Heute ein Uni-Text-LLM, morgen ein stärkeres Modell — gleiche Schnittstelle.

---

## 3. Ist "agentisch" hier sinnvoll? (Konzept-Klärung)

**Ja, mit Maß.** Agentisch heißt: Das System läuft in einer Schleife **Sense → Plan → Act** statt nur einmal Frage→Antwort.

```
   ┌─────────────────────────────────────────┐
   │                                         │
   ▼                                         │
SENSE  ──►  PLAN  ──►  ACT  ──►  (Ergebnis)──┘
Kamera+     LLM        Fahr-
Sensoren    entscheidet befehl
```

**Die wichtige Design-Regel:** Das LLM trifft **Entscheidungen** (wohin, was als Nächstes, Befehl interpretieren). Aber **Reflexe** (Hindernis < 20 cm → stopp) gehören in normalen Python-Code, nicht ins LLM. Sonst wird der Rover langsam (jeder LLM-Aufruf kostet 1-3 Sek) und teuer.

Faustregel: **LLM für Klugheit, Code für Schnelligkeit.**

---

## 4. Die drei Schichten (Modul-Architektur)

```
┌──────────────────────────────────────────────────────────┐
│  SCHICHT 3 — AGENT / GEHIRN            (Laptop)           │
│  Chat-Eingabe, Sense-Plan-Act-Loop, LLM-Aufrufe,         │
│  Karte verwalten, Wegfindung (Dijkstra/BFS)              │
└───────────────────────────┬──────────────────────────────┘
                            │ ruft auf
┌───────────────────────────▼──────────────────────────────┐
│  SCHICHT 2 — WAHRNEHMUNG               (Laptop)           │
│  perceive(image) -> Objekte    [YOLO, später Vision-LLM] │
└───────────────────────────┬──────────────────────────────┘
                            │ Kamera-Stream / Fahrbefehle
┌───────────────────────────▼──────────────────────────────┐
│  SCHICHT 1 — KÖRPER                    (Raspberry Pi)     │
│  Freenove-Server: Motoren, Servos, Sensoren, Kamera      │
└──────────────────────────────────────────────────────────┘
```

Jede Schicht hat eine **klare Schnittstelle** und kann unabhängig entwickelt/getestet werden. Das ist euer modularer Aufbau.

### Wer im Team was "besitzt"
- **Körper-Schicht (1):** 1 Person — hält Freenove-Server am Laufen, baut saubere Bewegungs-Befehle.
- **Wahrnehmungs-Schicht (2):** 1 Person — YOLO einrichten, `perceive()` bauen.
- **Gehirn-Schicht (3):** 1-2 Personen — Agent-Loop, LLM-Anbindung, Karte + Wegfindung.

---

## 5. Das "mentale Raummodell" — topologische Karte

Statt einer pixelgenauen Karte (sehr schwer) bauen wir einen **Graphen** — wie eine U-Bahn-Karte. Als Java-Leute kennt ihr Graphen.

- **Knoten (Node)** = markanter Ort, den der Rover bei der Erkundung erkennt
  ("Ecke mit Pflanze", "Tür", "Schreibtisch"). Wird durch erkannte Objekte + Position definiert.
- **Kante (Edge)** = Verbindung mit "Fahr-Kosten"
  ("von Pflanze zu Tür: 2,5 Sek geradeaus, dann 90° links").
- **Kürzester Weg** = Dijkstra oder BFS auf dem Graphen — Standard-Informatik.

So bekommt ihr Mapping UND Wegfindung, ohne SLAM-Mathematik. Das ist der Unterschied zwischen "in 3 Wochen machbar" und "unmöglich".

**Wie die Karte entsteht (Erkundungsfahrt):**
1. Rover dreht sich, macht Kamera-Schnappschüsse, YOLO erkennt Objekte.
2. Neue markante Orte werden als Knoten gespeichert (mit grober Richtung/Distanz).
3. Beim Weiterfahren werden Kanten zwischen Orten eingetragen.
4. Ergebnis: ein Graph, den das LLM "lesen" kann (als Text).

> **Realismus-Hinweis:** Ohne echte Lokalisierung driftet die Position über Zeit. Für eine überzeugende Demo in einem kleinen, aufgeräumten Raum reicht das. Erwartet keine Millimeter-Präzision — das ist bewusst so.

---

## 6. Technologie-Stack (konkrete Bibliotheken)

### Auf dem Raspberry Pi (Schicht 1)
| Zweck | Bibliothek | Anmerkung |
|---|---|---|
| Bewegung/Servos/Sensoren | **Freenove-Code** | schon vorhanden, kaum ändern |
| GPIO | `gpiozero`, `lgpio` | schon installiert |
| Kamera | `picamera2` | Standard auf Pi OS |
| Netzwerk | `socket` (stdlib) | Freenove nutzt das schon |

### Auf dem Laptop (Schicht 2 + 3)
| Zweck | Bibliothek | Anmerkung |
|---|---|---|
| Objekterkennung | **`ultralytics`** (YOLOv8/v11) | `pip install ultralytics`, vortrainiert, kostenlos |
| Bildverarbeitung | `opencv-python` | Kamera-Frames empfangen/anzeigen |
| LLM-Anbindung | `openai` SDK oder `requests` | Uni-API ist meist OpenAI-kompatibel |
| Graph + Wegfindung | `networkx` | Dijkstra/BFS fertig eingebaut |
| Konfiguration | `python-dotenv` | API-Keys aus `.env` lesen |

> **Hinweis zur Uni-API:** Die meisten Uni-LLM-Zugänge sprechen das **OpenAI-kompatible** Format (gleiche Endpunkt-Struktur, nur andere URL + Key). Dann könnt ihr das `openai`-SDK mit geänderter `base_url` nutzen. Bei Setup prüfen.

---

## 7. Repo-Struktur (aufbauend auf Freenove)

```
rover-project/
├── README.md                    # Setup-Anleitung
├── PROJECT_BLUEPRINT.md         # dieses Dokument
├── .env.example                 # Vorlage für API-Keys (ohne echte Keys!)
├── requirements.txt             # Laptop-Abhängigkeiten
│
├── pi/                          # === läuft auf dem Raspberry Pi ===
│   └── (Freenove Code/Server)   # weitgehend unverändert übernommen
│
├── laptop/                      # === läuft auf dem Laptop ===
│   ├── body/                    # SCHICHT 1: Brücke zum Pi
│   │   └── rover_client.py      # schickt Fahr-/Greifbefehle, holt Kamerabild
│   │
│   ├── perception/              # SCHICHT 2: Wahrnehmung
│   │   ├── perceiver.py         # perceive(image) -> Objekte   (Schnittstelle!)
│   │   └── yolo_perceiver.py    # YOLO-Implementierung
│   │
│   ├── brain/                   # SCHICHT 3: Agent
│   │   ├── agent.py             # Sense-Plan-Act-Loop
│   │   ├── llm.py               # decide(...) -> Aktion  (LLM-Anbindung)
│   │   ├── world_map.py         # Graph: Knoten, Kanten, Wegfindung
│   │   └── actions.py           # erlaubte Aktionen (fahre, drehe, greife...)
│   │
│   ├── config.py                # zentrale Einstellungen (IP, Pins, Schwellen)
│   └── main.py                  # Einstiegspunkt: startet Chat + Agent
│
└── tests/                       # kleine Testskripte je Modul
```

**Warum diese Struktur:**
- `pi/` und `laptop/` strikt getrennt — klar, was wo läuft.
- Jede Schicht ein eigener Ordner — Teammitglieder arbeiten parallel ohne Konflikte.
- `perceiver.py` und `llm.py` sind die **austauschbaren Schnittstellen** für späteres Upgrade.
- `config.py` zentral — keine verstreuten Magic Numbers.

---

## 8. 3-Wochen-Plan

### Woche 1 — Fundament & Fernsteuerung
**Ziel: Rover fährt zuverlässig auf Befehl vom Laptop, Kamerabild kommt an.**

- [ ] Repo aufsetzen, Struktur anlegen, Git-Workflow im Team klären
- [ ] Freenove-Server auf dem Pi stabil zum Laufen bringen (Autostart)
- [ ] `rover_client.py`: vom Laptop aus fahren/drehen/greifen (Schicht 1)
- [ ] Kamera-Stream Laptop empfängt + anzeigt (OpenCV)
- [ ] Saubere Bewegungs-Primitive definieren: `fahre(cm)`, `drehe(grad)`, `greife()`
- [ ] **Meilenstein:** Laptop-Skript steuert Rover komplett, Bild ist live

### Woche 2 — Sehen & Denken
**Ziel: Rover erkennt Objekte und reagiert auf einfache Textbefehle.**

- [ ] YOLO einrichten, `perceive()` liefert Objektliste aus Kamerabild (Schicht 2)
- [ ] Uni-LLM-API anbinden, `decide()` gibt eine Aktion zurück (Schicht 3)
- [ ] Erste Agent-Schleife: Chat-Befehl → LLM → eine Aktion → ausführen
- [ ] Reflexe in Code: Hindernis (Ultraschall) → automatischer Stopp
- [ ] **Meilenstein:** "dreh dich bis du eine Flasche siehst" funktioniert

### Woche 3 — Karte, Wegfindung & Politur
**Ziel: Erkundung, Karte, kürzester Weg, überzeugende Demo.**

- [ ] `world_map.py`: Graph aufbauen während Erkundungsfahrt
- [ ] Dijkstra/BFS für kürzesten Weg zu bekanntem Ort (`networkx`)
- [ ] Agent kann: erkunden → Objekt gefunden → Weg zurück/hin planen
- [ ] Demo-Szenario einüben, Fehlerfälle abfangen, Doku/README finalisieren
- [ ] Puffer für Unerwartetes (immer einplanen!)
- [ ] **Meilenstein:** vollständige Demo "finde Objekt X" im Testraum

> **Risiko-Hinweis:** Woche 3 ist am dichtesten. Falls es eng wird, ist die **Wegfindung** das erste, was vereinfacht werden kann (z.B. nur "zurück zum Start" statt beliebiger kürzester Weg). Die Kern-Demo (Objekt finden) muss stehen.

---

## 9. Erste konkrete Schritte (diese Woche)

1. **Repo + Struktur anlegen** (Ordner aus Abschnitt 7).
2. **VS Code Remote-SSH** zum Pi einrichten — dann entwickelt ihr bequem direkt auf dem Pi für die Körper-Schicht.
3. **Freenove-Server-Autostart** auf dem Pi, damit ihr nicht jedes Mal manuell starten müsst.
4. **`rover_client.py`** als Erstes bauen — die Brücke Laptop→Pi ist die Basis für alles Weitere.
5. **Uni-API-Zugang testen** mit einem 5-Zeilen-Skript ("sag Hallo"), bevor ihr ihn in den Agent einbaut.

---

## 10. Python für Java-Leute (Schnell-Brücke)

| Java | Python | Hinweis |
|---|---|---|
| `class A {}` | `class A:` | Einrückung statt `{}` |
| `void f(int x)` | `def f(x):` | keine Typen nötig (optional) |
| `List<String>` | `list` | dynamisch |
| `import` | `import` | ähnlich |
| `null` | `None` | |
| `System.out.println` | `print()` | |
| Maven/Gradle | `pip` + `requirements.txt` | |

Eure Java-Konzepte (OOP, Interfaces, Threads, Sockets, Graphen) übertragen sich 1:1. Python ist nur knapper geschrieben. Plant 1-2 Tage Eingewöhnung ein.

---

*Dieses Dokument ist die gemeinsame Arbeitsgrundlage. Bei Architektur-Änderungen hier aktualisieren, damit alle auf demselben Stand sind.*
