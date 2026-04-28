import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bungee Survival Calculator",
    page_icon="🪢",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Share+Tech+Mono&family=Inter:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    background-color: #0a0a0f;
    color: #e8e8e8;
}

.stApp {
    background: radial-gradient(ellipse at 20% 0%, #1a0a2e 0%, #0a0a0f 60%);
}

h1 {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 4rem !important;
    letter-spacing: 0.08em;
    background: linear-gradient(135deg, #ff3c3c, #ff8c00);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0 !important;
}

h2, h3 {
    font-family: 'Bebas Neue', sans-serif !important;
    letter-spacing: 0.06em;
    color: #ff8c00 !important;
}

.mono {
    font-family: 'Share Tech Mono', monospace;
}

.metric-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,140,0,0.25);
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 0.75rem;
    font-family: 'Share Tech Mono', monospace;
}

.metric-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #888;
    margin-bottom: 0.3rem;
}

.metric-value {
    font-size: 1.9rem;
    font-weight: 700;
    color: #ff8c00;
}

.metric-sub {
    font-size: 0.78rem;
    color: #aaa;
    margin-top: 0.2rem;
}

.survive-banner {
    background: linear-gradient(135deg, #0d3320, #0a2e18);
    border: 2px solid #00e676;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    margin: 1.5rem 0;
}

.die-banner {
    background: linear-gradient(135deg, #3a0a0a, #2e0a0a);
    border: 2px solid #ff1744;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    margin: 1.5rem 0;
}

.verdict-text {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.5rem;
    letter-spacing: 0.1em;
}

.risk-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.6rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.85rem;
}

.risk-safe   { color: #00e676; }
.risk-warn   { color: #ffea00; }
.risk-danger { color: #ff6d00; }
.risk-fatal  { color: #ff1744; }

.stSlider > div { padding-top: 0.2rem; }

div[data-testid="stRadio"] label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.9rem;
}

.subtitle {
    font-family: 'Share Tech Mono', monospace;
    color: #666;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
    margin-top: -0.5rem;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ── Physics constants ─────────────────────────────────────────────────────────
g       = 9.81        # m/s²
DROP_H  = 182.0       # metres
DT      = 0.001       # time step (s)

# Medical thresholds (literature-based)
BLACKOUT_G    = 4.0   # sustained G → grey-out / GLOC risk
SPINAL_G      = 6.0   # peak G → vertebral compression fracture risk
FATAL_G       = 15.0  # generally accepted lethal peak G for untrained person
SAFE_IMPACT   = 6.0   # m/s — safe landing / water-entry speed
FATAL_IMPACT  = 25.0  # m/s — unsurvivable impact

def simulate_bungee(mass_kg: float, cord_len: float) -> dict:
    """
    Simulate a bungee jump from DROP_H metres.
    Cord natural length = cord_len m.
    Spring constant k estimated so that at max stretch the restoring force
    equals ~3× body weight (reasonable commercial bungee).
    """
    k = (3 * mass_kg * g) / cord_len   # N/m  — stiffness

    # Drag coefficient (air): assume cross-section ~0.7 m², Cd~1.0, ρ=1.2 kg/m³
    C_drag = 0.5 * 1.0 * 1.2 * 0.7    # ≈ 0.42

    y       = DROP_H   # height above ground (starts at top)
    v       = 0.0      # velocity (positive = downward)
    t       = 0.0

    times, heights, velocities, accels = [], [], [], []

    max_g      = 0.0
    min_height = DROP_H
    bounces    = 0
    prev_v     = 0.0
    sim_time   = 60.0   # simulate up to 60 s

    while t < sim_time:
        stretch = max(0.0, (DROP_H - y) - cord_len)   # extension beyond natural len

        F_gravity = mass_kg * g                        # downward
        F_spring  = k * stretch                        # upward when cord taut
        F_drag    = C_drag * v * abs(v)                # opposes motion

        # Net force (down positive)
        F_net = F_gravity - F_spring - F_drag * np.sign(v)
        a     = F_net / mass_kg                        # m/s²

        # Felt G = (net upward force on body) / weight
        # When cord is taut the upward force is spring − drag_when_going_down
        upward_force = F_spring
        felt_g = upward_force / (mass_kg * g)          # in G units

        times.append(t)
        heights.append(y)
        velocities.append(v)
        accels.append(felt_g)

        # Track extremes
        if felt_g > max_g:
            max_g = felt_g
        if y < min_height:
            min_height = y

        # Count direction reversals (bounces)
        if prev_v < 0 and v >= 0:
            bounces += 1

        prev_v = v

        # Euler integration
        v += a * DT
        y -= v * DT          # y decreases as jumper falls

        # Ground check
        if y <= 0:
            y = 0
            break

        t += DT

    return {
        "times":       np.array(times),
        "heights":     np.array(heights),
        "velocities":  np.array(velocities),
        "accels":      np.array(accels),
        "max_g":       max_g,
        "min_height":  min_height,
        "max_speed":   float(np.max(np.abs(velocities))),
        "bounces":     bounces,
        "cord_k":      k,
        "hit_ground":  min_height <= 0.5,
    }


def medical_breakdown(sim: dict, mass_kg: float, cord_len: float):
    max_g      = sim["max_g"]
    max_speed  = sim["max_speed"]
    min_h      = sim["min_height"]
    hit_ground = sim["hit_ground"]

    risks = []

    # 1. Blackout / GLOC
    if max_g < BLACKOUT_G:
        risks.append(("Grey-out / GLOC risk", f"{max_g:.1f} G  <  {BLACKOUT_G} G threshold", "safe",
                      "G-forces are below the grey-out threshold for the general population."))
    elif max_g < SPINAL_G:
        risks.append(("Grey-out / GLOC risk", f"{max_g:.1f} G  ⚠  threshold {BLACKOUT_G} G", "warn",
                      "You may experience tunnel vision or brief loss of consciousness on snap-back."))
    else:
        risks.append(("Grey-out / GLOC risk", f"{max_g:.1f} G  ✕  threshold {BLACKOUT_G} G", "danger",
                      "High probability of G-induced Loss Of Consciousness (GLOC) at cord snap."))

    # 2. Spinal compression
    if max_g < SPINAL_G:
        risks.append(("Spinal compression fracture", f"{max_g:.1f} G  <  {SPINAL_G} G threshold", "safe",
                      "Peak G is below vertebral compression fracture risk for a healthy spine."))
    elif max_g < FATAL_G:
        risks.append(("Spinal compression fracture", f"{max_g:.1f} G  ⚠  threshold {SPINAL_G} G", "warn",
                      "Significant risk of vertebral micro-fractures or disc herniation, especially lumbar."))
    else:
        risks.append(("Spinal compression fracture", f"{max_g:.1f} G  ✕  threshold {SPINAL_G} G", "fatal",
                      "Peak G exceeds documented spinal fracture threshold. Paralysis risk is high."))

    # 3. Retinal haemorrhage (bungee-specific)
    if max_g < 3.0:
        risks.append(("Retinal haemorrhage", f"{max_g:.1f} G  <  3 G threshold", "safe",
                      "Eye pressure from G-loading is within tolerable range."))
    elif max_g < 8.0:
        risks.append(("Retinal haemorrhage", f"{max_g:.1f} G  ⚠  threshold 3 G", "warn",
                      "Elevated intraocular pressure at snap-back; risk of subconjunctival bleeding."))
    else:
        risks.append(("Retinal haemorrhage", f"{max_g:.1f} G  ✕  threshold 8 G", "fatal",
                      "Severe retinal haemorrhage likely. Vision loss risk is significant."))

    # 4. Ground strike
    if hit_ground:
        risks.append(("Ground / water strike", f"Min height: {min_h:.1f} m  ✕  CORD TOO SHORT", "fatal",
                      "The cord does not arrest the fall in time — you hit the ground. Fatal."))
    elif min_h < 2.0:
        risks.append(("Ground / water strike", f"Min height: {min_h:.1f} m  ⚠  dangerously close", "danger",
                      "Clearance is less than 2 m — any miscalculation or cord stretch would be fatal."))
    else:
        risks.append(("Ground / water strike", f"Clearance: {min_h:.1f} m  ✓  safe", "safe",
                      "Adequate clearance from ground."))

    # 5. Peak G overall survival
    if max_g >= FATAL_G:
        risks.append(("Overall G-force survival", f"{max_g:.1f} G  ✕  fatal threshold {FATAL_G} G", "fatal",
                      "Peak deceleration exceeds what the human body can survive."))
    elif max_g >= SPINAL_G:
        risks.append(("Overall G-force survival", f"{max_g:.1f} G  ⚠  severe injury likely", "danger",
                      "Likely serious injuries but survivable with immediate medical attention."))
    else:
        risks.append(("Overall G-force survival", f"{max_g:.1f} G  ✓  within survivable range", "safe",
                      "G-forces are within the range seen in commercial bungee operations."))

    return risks


def overall_verdict(sim: dict) -> tuple[bool, str]:
    max_g     = sim["max_g"]
    hit_ground = sim["hit_ground"]
    min_h     = sim["min_height"]

    if hit_ground or min_h < 0.5:
        return False, "You hit the ground. Physics wins."
    if max_g >= FATAL_G:
        return False, f"Peak G-force of {max_g:.1f} G exceeds human survivability."
    if max_g >= SPINAL_G:
        return True, f"Survivable — but {max_g:.1f} G means severe injuries are likely."
    return True, f"You survive with {max_g:.1f} G peak force and {sim['min_height']:.1f} m clearance."


# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("<h1>BUNGEE SURVIVAL CALCULATOR</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">// 182 METRE DROP · FULL MEDICAL RISK ANALYSIS · NEWTONIAN PHYSICS</p>',
            unsafe_allow_html=True)

col_input, col_results = st.columns([1, 2], gap="large")

with col_input:
    st.markdown("### INPUT PARAMETERS")

    mass = st.slider("**Body weight (kg)**", min_value=40, max_value=200,
                     value=75, step=1, format="%d kg")

    cord_choice = st.radio(
        "**Cord length**",
        options=["30 m", "45 m", "60 m"],
        index=1,
        help="Natural (unstretched) length of the bungee cord"
    )
    cord_len = float(cord_choice.split()[0])

    st.markdown("")
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Drop height</div>
        <div class="metric-value">182 m</div>
        <div class="metric-sub">Macau Tower equivalent</div>
    </div>
    <div class="metric-box">
        <div class="metric-label">Cord natural length</div>
        <div class="metric-value">{cord_len:.0f} m</div>
        <div class="metric-sub">Stretch zone: {182 - cord_len:.0f} m</div>
    </div>
    <div class="metric-box">
        <div class="metric-label">Jumper mass</div>
        <div class="metric-value">{mass} kg</div>
        <div class="metric-sub">Weight: {mass * 9.81:.0f} N</div>
    </div>
    """, unsafe_allow_html=True)

# Run simulation
sim = simulate_bungee(mass, cord_len)
survived, verdict_msg = overall_verdict(sim)
risks = medical_breakdown(sim, mass, cord_len)

with col_results:
    # Verdict banner
    if survived:
        st.markdown(f"""
        <div class="survive-banner">
            <div class="verdict-text" style="color:#00e676;">✓ YOU SURVIVE</div>
            <div style="font-family:'Share Tech Mono',monospace; color:#aaa; margin-top:0.5rem; font-size:0.9rem;">
                {verdict_msg}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="die-banner">
            <div class="verdict-text" style="color:#ff1744;">✕ YOU DO NOT SURVIVE</div>
            <div style="font-family:'Share Tech Mono',monospace; color:#aaa; margin-top:0.5rem; font-size:0.9rem;">
                {verdict_msg}
            </div>
        </div>""", unsafe_allow_html=True)

    # Key stats row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-box">
            <div class="metric-label">Peak G-force</div>
            <div class="metric-value" style="color:{'#ff1744' if sim['max_g']>=FATAL_G else '#ff8c00'};">{sim['max_g']:.1f} G</div>
            <div class="metric-sub">at cord snap-back</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-box">
            <div class="metric-label">Max speed</div>
            <div class="metric-value">{sim['max_speed']:.1f} m/s</div>
            <div class="metric-sub">{sim['max_speed']*3.6:.0f} km/h</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        color = "#ff1744" if sim['min_height'] < 1 else ("#ff8c00" if sim['min_height'] < 3 else "#00e676")
        st.markdown(f"""<div class="metric-box">
            <div class="metric-label">Min clearance</div>
            <div class="metric-value" style="color:{color};">{sim['min_height']:.1f} m</div>
            <div class="metric-sub">above ground</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-box">
            <div class="metric-label">Bounces</div>
            <div class="metric-value">{sim['bounces']}</div>
            <div class="metric-sub">oscillations</div>
        </div>""", unsafe_allow_html=True)

    # Charts
    st.markdown("### FLIGHT PROFILE")

    # Downsample for speed
    step = max(1, len(sim["times"]) // 2000)
    t  = sim["times"][::step]
    h  = sim["heights"][::step]
    v  = sim["velocities"][::step]
    ag = sim["accels"][::step]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        subplot_titles=("Height above ground (m)", "G-force felt by jumper"),
        vertical_spacing=0.12,
    )

    fig.add_trace(go.Scatter(
        x=t, y=h, mode="lines", name="Height",
        line=dict(color="#ff8c00", width=2),
        fill="tozeroy", fillcolor="rgba(255,140,0,0.08)"
    ), row=1, col=1)

    # Add cord engagement line
    cord_engage_height = DROP_H - cord_len
    fig.add_hline(y=cord_engage_height, line_dash="dot", line_color="rgba(255,255,255,0.3)",
                  annotation_text=f"Cord engages ({cord_engage_height:.0f} m)",
                  annotation_font_color="rgba(255,255,255,0.5)",
                  row=1, col=1)

    # G-force with thresholds
    fig.add_trace(go.Scatter(
        x=t, y=ag, mode="lines", name="G-force",
        line=dict(color="#ff3c3c", width=2),
    ), row=2, col=1)

    for thresh, label, col in [
        (BLACKOUT_G, "Blackout threshold (4 G)", "rgba(255,234,0,0.6)"),
        (SPINAL_G,   "Spinal risk (6 G)",         "rgba(255,109,0,0.6)"),
        (FATAL_G,    "Fatal threshold (15 G)",     "rgba(255,23,68,0.7)"),
    ]:
        fig.add_hline(y=thresh, line_dash="dot", line_color=col,
                      annotation_text=label, annotation_font_color=col,
                      row=2, col=1)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.03)",
        font=dict(family="Share Tech Mono, monospace", color="#aaa", size=11),
        showlegend=False,
        margin=dict(l=10, r=10, t=40, b=10),
        height=480,
    )
    fig.update_xaxes(
        showgrid=True, gridcolor="rgba(255,255,255,0.06)",
        tickfont=dict(color="#666"), title_text="Time (s)", row=2, col=1
    )
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)",
                     tickfont=dict(color="#666"))

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Medical breakdown
    st.markdown("### MEDICAL RISK BREAKDOWN")

    risk_css = {"safe": "risk-safe", "warn": "risk-warn", "danger": "risk-danger", "fatal": "risk-fatal"}
    risk_icon = {"safe": "✓", "warn": "⚠", "danger": "⚠⚠", "fatal": "✕"}

    for name, value, level, desc in risks:
        css = risk_css[level]
        icon = risk_icon[level]
        st.markdown(f"""
        <div class="risk-item">
            <div>
                <span class="{css}" style="font-weight:700;">{icon} {name}</span><br>
                <span style="color:#666; font-size:0.78rem;">{desc}</span>
            </div>
            <div class="{css}" style="text-align:right; white-space:nowrap; margin-left:1rem;">{value}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""<div style="font-family:'Share Tech Mono',monospace; font-size:0.7rem; color:#444; border-top:1px solid #1a1a1a; padding-top:0.75rem;">
    DISCLAIMER: This is a physics simulation for educational purposes only. Bungee jumping should only be performed 
    with certified operators using professional equipment. Medical thresholds are population averages and vary 
    significantly with age, fitness, and pre-existing conditions. Sources: FAA G-tolerance studies, 
    spinal biomechanics literature (Nightingale et al.), and commercial bungee operator safety protocols.
    </div>""", unsafe_allow_html=True)
