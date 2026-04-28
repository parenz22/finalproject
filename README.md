# 🪢 Bungee Survival Calculator

A physics-based Streamlit app that simulates a **182-metre bungee jump**, calculates height and G-forces over time, and tells you — with a full medical breakdown — whether you survive.

---

## Requirements

- Python 3.8 or higher
- pip

---

## Installation

**1. Clone or download the project**

Place `bungee_jump.py` in a folder of your choice, then open a terminal in that folder.

**2. (Optional but recommended) Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

**3. Install dependencies**

```bash
pip install streamlit plotly numpy
```

---

## Running the App

```bash
streamlit run bungee_jump.py
```

Streamlit will print a local URL — open it in your browser:

```
Local URL:  http://localhost:8501
```

---

## How to Use

| Control | Description |
|---|---|
| **Body weight slider** | Set your weight in kg (40–200 kg) |
| **Cord length radio** | Choose 30 m, 45 m, or 60 m cord |

The app updates instantly as you adjust the controls.

---

## What the App Shows

**Survival verdict** — a clear SURVIVE / DO NOT SURVIVE banner with the reason.

**Key stats** — peak G-force, max speed, minimum ground clearance, and number of bounces.

**Flight profile charts:**
- Height above ground vs time (with cord engagement marker)
- G-force felt by the jumper vs time (with medical threshold lines)

**Medical risk breakdown** across 5 categories:
- Grey-out / G-induced Loss of Consciousness (GLOC)
- Spinal compression fracture
- Retinal haemorrhage
- Ground strike clearance
- Overall G-force survivability

---

## Physics Model

The simulation uses Euler integration with:

- **Gravity** — 9.81 m/s²
- **Bungee cord** — Hooke's law spring; stiffness `k` is calculated so the cord exerts ~3× body weight at full extension, matching commercial bungee specs
- **Air drag** — modelled with a drag coefficient of ~0.42 (cross-section 0.7 m², Cd = 1.0, air density 1.2 kg/m³)
- **Time step** — 1 ms for accuracy

---

## Medical Thresholds Used

| Threshold | G-force | Source basis |
|---|---|---|
| Grey-out / GLOC | 4 G | FAA G-tolerance studies |
| Spinal fracture risk | 6 G | Nightingale et al., spinal biomechanics |
| Retinal haemorrhage | 3–8 G | Bungee injury case literature |
| Fatal G-force | 15 G | Generally accepted human survivability limit |

> **Disclaimer:** This is a physics simulation for educational purposes only. Medical thresholds are population averages and vary with age, fitness, and pre-existing conditions. Never attempt bungee jumping outside of a certified operator environment.

---

## Troubleshooting

**`ModuleNotFoundError`** — make sure you installed dependencies in the same Python environment you're running the app from. If using a virtual environment, confirm it's activated.

**Port already in use** — run on a different port:
```bash
streamlit run bungee_jump.py --server.port 8502
```

**Slow on first load** — the physics simulation runs ~60,000 iterations; this is normal and takes under a second on most machines.
