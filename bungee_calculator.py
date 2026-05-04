import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bungee Survival Calculator - Excel Sync",
    page_icon="🪢",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Share+Tech+Mono&family=Inter:wght@300;400;600&display=swap');
html, body, [class*="css"] { background-color: #0a0a0f; color: #e8e8e8; }
.stApp { background: radial-gradient(ellipse at 20% 0%, #1a0a2e 0%, #0a0a0f 60%); }
h1 { font-family: 'Bebas Neue', sans-serif !important; font-size: 4rem !important; letter-spacing: 0.08em; background: linear-gradient(135deg, #ff3c3c, #ff8c00); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0 !important; }
h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 0.06em; color: #ff8c00 !important; }
.metric-box { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,140,0,0.25); border-radius: 8px; padding: 1.2rem 1.5rem; margin-bottom: 0.75rem; font-family: 'Share Tech Mono', monospace; }
.metric-label { font-size: 0.72rem; text-transform: uppercase; color: #888; margin-bottom: 0.3rem; }
.metric-value { font-size: 1.9rem; font-weight: 700; color: #ff8c00; }
.metric-sub { font-size: 0.78rem; color: #aaa; }
.survive-banner { background: linear-gradient(135deg, #0d3320, #0a2e18); border: 2px solid #00e676; border-radius: 12px; padding: 2rem; text-align: center; margin: 1.5rem 0; }
.die-banner { background: linear-gradient(135deg, #3a0a0a, #2e0a0a); border: 2px solid #ff1744; border-radius: 12px; padding: 2rem; text-align: center; margin: 1.5rem 0; }
.verdict-text { font-family: 'Bebas Neue', sans-serif; font-size: 3.5rem; }
.risk-item { display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0; border-bottom: 1px solid rgba(255,255,255,0.06); font-family: 'Share Tech Mono', monospace; font-size: 0.85rem; }
.risk-safe { color: #00e676; } .risk-warn { color: #ffea00; } .risk-danger { color: #ff6d00; } .risk-fatal { color: #ff1744; }
.subtitle { font-family: 'Share Tech Mono', monospace; color: #666; font-size: 0.85rem; margin-top: -0.5rem; margin-bottom: 2rem; }
</style>
""", unsafe_allow_html=True)

# ── Physics Constants & Simulation ────────────────────────────────────────────
G_ACCEL = 9.81
DROP_H  = 182.0 # Macau Tower height

def simulate_bungee_excel(m, L, E, d, c_d, dt):
    """
    Solves: dv/dt = g - (c_d/m)*v|v| - (k/m)*max(0, y - L)
    m: mass (kg), L: natural length (m), E: Young's Modulus (Pa)
    d: diameter (m), c_d: drag coefficient, dt: time step (s)
    y: displacement downward from jump point (positive = down)
    """
    A = np.pi * (d / 2)**2
    k = (E * A) / L

    # State variables: y=0 at jump point, positive downward
    y = 0.0
    v = 0.0
    t = 0.0

    sim_time = 40.0
    times, positions, velocities, gs = [], [], [], []

    while t < sim_time:
        # Compute stretch and acceleration from the ODE:
        # dv/dt = g - (c_d/m)*v|v| - (k/m)*max(0, y-L)
        stretch = max(0.0, y - L)
        a = G_ACCEL - (c_d / m) * v * abs(v) - (k / m) * stretch

        # Felt G-force: net upward restoring force / (m*g)
        f_spring = k * stretch
        f_drag = c_d * v * abs(v)
        felt_g = (f_spring + f_drag) / (m * G_ACCEL)

        times.append(t)
        positions.append(y)
        velocities.append(v)
        gs.append(felt_g)

        # Euler update (matches Excel: use current values to step forward)
        y = y + v * dt
        v = v + a * dt

        # Ground check
        if (DROP_H - y) <= 0:
            break
        t += dt

    return {
        "times": np.array(times),
        "heights": DROP_H - np.array(positions),  # Convert displacement to height above ground
        "velocities": np.array(velocities),
        "gs": np.array(gs),
        "max_g": np.max(gs),
        "min_height": DROP_H - np.max(positions),
        "max_speed": np.max(np.abs(velocities)),
        "k_value": k
    }

# ── UI Layout ─────────────────────────────────────────────────────────────────
st.markdown("<h1>BUNGEE SURVIVAL CALCULATOR</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">// EXCEL-SYNCHRONIZED PHYSICS · PROJECT 3</p>', unsafe_allow_html=True)

col_input, col_results = st.columns([1, 2], gap="large")

with col_input:
    st.markdown("### INPUT PARAMETERS")
    m = st.slider("**Mass of Jumper (kg)**", 40, 150, 90)
    L = st.slider("**Cord Natural Length (m)**", 10, 100, 30)
    E = st.number_input("**Young's Modulus (E)**", value=700000, step=50000, help="Elasticity of the cord material")
    d = st.number_input("**Cord Diameter (m)**", value=0.05, step=0.01, format="%.2f")
    c_d = st.slider("**Drag Coefficient (cₐ)**", 0, 20, 5)
    dt = st.selectbox("**Time Step (dt)**", [0.01, 0.001], index=0)

    sim = simulate_bungee_excel(m, L, E, d, c_d, dt)
    
    st.markdown(f"""
    <div class="metric-box">
        <div class="metric-label">Calculated Stiffness (k)</div>
        <div class="metric-value">{sim['k_value']:.2f} N/m</div>
        <div class="metric-sub">Based on E, A, and L</div>
    </div>
    """, unsafe_allow_html=True)

with col_results:
    # Verdict
    survived = sim['min_height'] > 0.5 and sim['max_g'] < 15.0
    if survived:
        st.markdown('<div class="survive-banner"><div class="verdict-text" style="color:#00e676;">✓ SURVIVED</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="die-banner"><div class="verdict-text" style="color:#ff1744;">✕ FATAL</div></div>', unsafe_allow_html=True)

    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-box"><div class="metric-label">Peak G-Force</div><div class="metric-value">{sim["max_g"]:.2f} G</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-box"><div class="metric-label">Max Speed</div><div class="metric-value">{sim["max_speed"]:.1f} m/s</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-box"><div class="metric-label">Min Clearance</div><div class="metric-value">{sim["min_height"]:.1f} m</div></div>', unsafe_allow_html=True)

    # Plotting
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
    fig.add_trace(go.Scatter(x=sim["times"], y=sim["heights"], name="Height (m)", line=dict(color="#ff8c00")), row=1, col=1)
    fig.add_trace(go.Scatter(x=sim["times"], y=sim["gs"], name="G-Force", line=dict(color="#ff3c3c")), row=2, col=1)
    
    fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.03)", font=dict(color="#aaa"), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)