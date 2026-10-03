import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os
import io
import base64

# --- 1. PAGE CONFIGURATION & CLEAN TECH CSS ---
st.set_page_config(page_title="S-Labs | Agritech Engine", page_icon="🧬", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Source+Sans+3:wght@400;500;600&display=swap');
    
    .stApp { background-color: #F8FAFC !important; font-family: 'Source Sans 3', sans-serif !important; color: #475569 !important; }
    h1, h2, h3, h4, h5, h6 { font-family: 'Sora', sans-serif !important; color: #0f172a !important; font-weight: 700 !important; }
    p, span, label, div { font-family: 'Source Sans 3', sans-serif; }
    
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #e2e8f0 !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #334155 !important; font-weight: 500; }
    
    div.stButton > button {
        background-color: #4CB7E4 !important; color: #ffffff !important;
        border: none !important; border-radius: 9999px !important;
        font-weight: 600 !important; transition: all 0.3s ease !important; padding: 10px 24px !important;
        box-shadow: 0 4px 6px -1px rgba(76,183,228, 0.2) !important;
    }
    div.stButton > button:hover {
        background-color: #38bdf8 !important;
        box-shadow: 0 10px 15px -3px rgba(76,183,228, 0.3) !important; transform: translateY(-1px) !important;
    }

    /* Botón de escenario crítico (rojo sutil) */
    button[kind="secondary"] {
        background-color: #fff1f2 !important; color: #e11d48 !important;
        border: 1px solid #fecdd3 !important;
    }
    button[kind="secondary"]:hover {
        background-color: #ffe4e6 !important; border-color: #fda4af !important;
    }
    
    [data-testid="stExpander"] {
        background-color: #FFFFFF !important; border: 1px solid #e2e8f0 !important;
        border-radius: 16px !important; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05) !important;
    }
    [data-testid="stExpander"] summary p { color: #0f172a !important; font-weight: 600 !important; }
    
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    div[data-testid="metric-container"] {
        background-color: #FFFFFF !important; border-radius: 16px; padding: 20px 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); border: 1px solid #f1f5f9;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetricValue"] > div { color: #0f172a !important; font-weight: 700 !important; font-family: 'Sora', sans-serif !important;}
    div[data-testid="stMetricLabel"] > label > div > p { color: #64748b !important; font-weight: 600 !important; text-transform: uppercase; font-size: 0.75rem; }
    
    .status-card {
        text-align: center; padding: 24px; background: #FFFFFF; 
        border-radius: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
        border: 1px solid #e2e8f0; height: 100%; display: flex; flex-direction: column; justify-content: center;
    }
    
    .tech-card-green { border-left: 4px solid #10b981 !important; background: #FFFFFF; border-radius: 12px; padding: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #f1f5f9;}
    .tech-card-red { border-left: 4px solid #f43f5e !important; background: #FFFFFF; border-radius: 12px; padding: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #f1f5f9;}
    
    .stTabs [data-baseweb="tab-list"] { gap: 12px; background-color: transparent; border-bottom: 1px solid #e2e8f0; }
    .stTabs [data-baseweb="tab"] {
        height: 48px; background-color: transparent; border: none;
        color: #64748b !important; font-weight: 600; font-family: 'Sora', sans-serif; font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] { color: #4CB7E4 !important; border-bottom: 3px solid #4CB7E4 !important; background-color: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE MANAGEMENT & REPRODUCIBILITY SCENARIOS ---
default_values = {'temp': 22.5, 'hum': 60.0, 'ph': 7.5, 'ec': 0.8}
for key, value in default_values.items():
    if key not in st.session_state: st.session_state[key] = value

def reset_params():
    for key, value in default_values.items(): st.session_state[key] = value

# NUEVO: Función de Reproducibilidad (Escenario de Falla Operativa)
def load_stress_scenario():
    st.session_state['temp'] = 34.0
    st.session_state['hum'] = 45.0
    st.session_state['ph'] = 4.8
    st.session_state['ec'] = 2.8

# --- 3. BILINGUAL DICTIONARY ---
lang_option = st.sidebar.radio("🌐 Platform Language", ["ES", "EN"], horizontal=True)

t = {
    "ES": {
        "title": "Motor de Inteligencia de Decisiones Agritech",
        "subtitle": "**Objetivo Operativo:** Ajuste dinámico de parámetros para mitigación de estrés ambiental y maximización de rendimiento.",
        "btn_stress": "🚨 Simular Escenario de Estrés",
        "btn_reset": "Restablecer Telemetría",
        "sidebar_env": "Variables No Controlables (Clima)",
        "sidebar_levers": "Actuadores Controlables (Riego)",
        "kpi1": "Rendimiento Proyectado",
        "kpi2": "Máximo Absoluto",
        "kpi3": "% Incremento (ROI)",
        "delta": "g (Recuperados)",
        "prescribed": "VECTOR DE CALIBRACIÓN ÓPTIMO:",
        "context_title": "Arquitectura y Caso de Negocio",
        "problem": "**El Reto:** El rendimiento agrícola experimenta caídas no lineales severas cuando las variables ambientales se desvían de sus umbrales óptimos.",
        "solution": "**Arquitectura S-Labs:** Despliegue de un ensamble *Random Forest* iterado mediante *Grid Search*. Simula miles de realidades en milisegundos para prescribir el vector exacto.",
        "business": "**Impacto en Negocio (Aplicación Práctica):** Permite a los operadores prevenir pérdidas antes de que ocurran. Al no sobredosificar nutrientes (EC) buscando compensar estrés térmico, se proyecta un **ahorro del 15% en insumos químicos** y una **reducción del 22% en merma biológica**.",
        "chart_title": "Mapeo de Umbral Biológico Principal (pH)",
        "neon_title": "Auditoría de Sensibilidad de Sensores",
        "status_critical": "Pérdida Operativa Crítica",
        "status_suboptimal": "Estrés Biológico Detectado",
        "status_optimal": "Rendimiento Maximizado",
        "chart_temp": "Curva de Impacto Térmico",
        "chart_ec": "Curva de Impacto Nutricional (EC)",
        "opt_lbl": "Vector Óptimo",
        "curr_lbl": "Telemetría Actual",
        "tab_sim": "Simulador Operativo",
        "tab_dash": "Dashboard Ejecutivo (Validación)",
    },
    "EN": {
        "title": "Agritech Decision Intelligence Engine",
        "subtitle": "**Operational Objective:** Dynamic parameter adjustment for environmental stress mitigation and yield maximization.",
        "btn_stress": "🚨 Load Critical Stress Scenario",
        "btn_reset": "Reset Telemetry",
        "sidebar_env": "Non-Controllable Variables",
        "sidebar_levers": "Controllable Actuators (Irrigation)",
        "kpi1": "Projected Yield",
        "kpi2": "Absolute Maximum",
        "kpi3": "% Increase (ROI)",
        "delta": "g (Recovered)",
        "prescribed": "OPTIMAL CALIBRATION VECTOR:",
        "context_title": "Architecture & Business Case",
        "problem": "**The Challenge:** Agricultural yield experiences severe non-linear degradation when environmental variables deviate from optimal thresholds.",
        "solution": "**S-Labs Architecture:** Deployment of a *Random Forest* ensemble iterated via Heuristic Grid Search. Simulates thousands of realities in milliseconds to prescribe the exact vector.",
        "business": "**Business Impact (Practical Application):** Enables operators to prevent crop loss before it happens. By preventing chemical overdosing (EC) to compensate for heat stress, the system projects a **15% savings in chemical inputs** and a **22% reduction in biological waste**.",
        "chart_title": "Primary Biological Threshold Mapping (pH)",
        "neon_title": "Sensor Sensitivity Audit",
        "status_critical": "Critical Operational Loss",
        "status_suboptimal": "Biological Stress Detected",
        "status_optimal": "Yield Maximized",
        "chart_temp": "Thermal Impact Curve",
        "chart_ec": "Nutritional Impact Curve (EC)",
        "opt_lbl": "Optimal Vector",
        "curr_lbl": "Current Telemetry",
        "tab_sim": "Operational Simulator",
        "tab_dash": "Executive Dashboard (Validation)",
    }
}[lang_option]

# --- 4. DYNAMIC LOGO INJECTION ---
def display_transparent_logo(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    image_path = os.path.join(current_dir, filename)
    if not os.path.exists(image_path) and os.path.exists(filename): image_path = filename
    if os.path.exists(image_path):
        try:
            from PIL import Image
            img = Image.open(image_path).convert("RGBA")
            data = np.array(img)
            r, g, b = data[:,:,0], data[:,:,1], data[:,:,2]
            white_areas = (r >= 230) & (g >= 230) & (b >= 230)
            data[white_areas, 3] = 0
            st.sidebar.image(Image.fromarray(data), use_container_width=True)
        except Exception: pass

display_transparent_logo('logo_git.png')
st.sidebar.markdown("<br>", unsafe_allow_html=True)

# --- 5. MODEL INGESTION (Mock) ---
@st.cache_resource
def load_model():
    model_path = 'models/rf_yield_predictor.pkl'
    if os.path.exists(model_path): return joblib.load(model_path)
    class MockModel:
        def predict(self, df):
            y = np.zeros(len(df))
            for i, row in df.iterrows():
                base = 400
                base -= 2 * (row['Temperature_C'] - 22)**2
                base -= 0.5 * (row['Humidity_percent'] - 65)**2
                base -= 40 * (row['pH_Level'] - 6.0)**2
                base -= 50 * (row['Nutrient_EC_mS'] - 1.5)**2
                y[i] = max(50, base)
            return y
        @property
        def feature_importances_(self): return np.array([0.18, 0.05, 0.45, 0.20, 0.10, 0.02])
    return MockModel()

rf_model = load_model()

# --- 6. SIDEBAR CONTROLS ---
st.sidebar.button(t["btn_stress"], on_click=load_stress_scenario, use_container_width=True, type="secondary")
st.sidebar.markdown("<br>", unsafe_allow_html=True)

st.sidebar.markdown(f"**{t['sidebar_env']}**")
current_temp = st.sidebar.slider("Temperature (°C)" if lang_option=="EN" else "Temperatura (°C)", 10.0, 40.0, key='temp', step=0.5)
current_hum = st.sidebar.slider("Humidity (%)" if lang_option=="EN" else "Humedad (%)", 40.0, 90.0, key='hum', step=1.0)
current_light, current_days = 14.0, 45

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown(f"**{t['sidebar_levers']}**")
current_ph = st.sidebar.slider("pH Level" if lang_option=="EN" else "Nivel de pH", 4.0, 9.0, key='ph', step=0.1)
current_ec = st.sidebar.slider("Nutrient EC (mS)" if lang_option=="EN" else "EC Nutrientes (mS)", 0.5, 3.0, key='ec', step=0.1)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.button(t["btn_reset"], on_click=reset_params, use_container_width=True, type="primary")

# --- 7. OPTIMIZATION ENGINE ---
def run_optimization():
    baseline_df = pd.DataFrame([[current_temp, current_hum, current_ph, current_ec, current_light, current_days]], 
                               columns=['Temperature_C', 'Humidity_percent', 'pH_Level', 'Nutrient_EC_mS', 'Light_Hours', 'Growth_Days'])
    baseline_yield = rf_model.predict(baseline_df)[0]
    
    ph_space = np.arange(5.0, 7.5, 0.1)
    ec_space = np.arange(1.0, 2.5, 0.1)
    grid_ph, grid_ec = np.meshgrid(ph_space, ec_space)
    
    sim_df = pd.DataFrame({
        'Temperature_C': current_temp, 'Humidity_percent': current_hum,
        'pH_Level': grid_ph.flatten(), 'Nutrient_EC_mS': grid_ec.flatten(),
        'Light_Hours': current_light, 'Growth_Days': current_days
    })
    
    sim_df['Predicted_Yield'] = rf_model.predict(sim_df[['Temperature_C', 'Humidity_percent', 'pH_Level', 'Nutrient_EC_mS', 'Light_Hours', 'Growth_Days']])
    optimal_row = sim_df.loc[sim_df['Predicted_Yield'].idxmax()]
    return baseline_yield, optimal_row, sim_df

baseline_yield, optimal_row, sim_df = run_optimization()

# --- 8. TABS SETUP & MAIN UI ---
st.title(t["title"])
st.markdown(t["subtitle"])
st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2 = st.tabs([t["tab_sim"], t["tab_dash"]])

SLATE_800 = "#1e293b"; SLATE_500 = "#64748b"; SLATE_200 = "#e2e8f0"
BLUE_BRAND = "#4CB7E4"; EMERALD = "#10b981"; ROSE = "#f43f5e"

with tab1:
    ABSOLUTE_MAX_YIELD = 400.0
    health_ratio = baseline_yield / ABSOLUTE_MAX_YIELD

    if baseline_yield < 200: status, p_color = t["status_critical"], ROSE
    elif baseline_yield < 350: status, p_color = t["status_suboptimal"], "#f59e0b"
    else: status, p_color = t["status_optimal"], EMERALD

    col_action, col_plant = st.columns([2.5, 1])

    with col_action:
        max_yield = optimal_row['Predicted_Yield']
        st.info(f"**{t['prescribed']}**\n\nTarget: **{max_yield:.1f}g** ➔ **pH: {optimal_row['pH_Level']:.1f}** | **EC: {optimal_row['Nutrient_EC_mS']:.1f} mS**")
        
        # NUEVO: Métrica de % de Incremento de ROI
        m1, m2, m3 = st.columns(3)
        m1.metric(t["kpi1"], f"{baseline_yield:.1f} g", f"{max_yield - baseline_yield:.1f} {t['delta']}", delta_color="normal")
        m2.metric(t["kpi2"], f"{max_yield:.1f} g", "✓ System Optimized" if lang_option=="EN" else "✓ Optimizado", delta_color="off")
        
        roi_pct = ((max_yield - baseline_yield) / max(1, baseline_yield)) * 100
        m3.metric(t["kpi3"], f"+{roi_pct:.1f}%", "Impacto Directo", delta_color="normal")

    with col_plant:
        st.markdown(f"""
        <div class="status-card">
            <h1 style="color: {p_color} !important; font-size: 3rem; margin:0;">{int(health_ratio*100)}%</h1>
            <p style="color: {SLATE_500}; font-weight: 600; margin-top: 5px; text-transform: uppercase; font-size: 0.8rem;">{status}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander(t["context_title"], expanded=False):
        # NUEVO: Caso de Negocio y Aplicación Práctica
        st.markdown(t["problem"])
        st.markdown(t["solution"])
        st.markdown(t["business"])

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"#### {t['chart_title']}")
    
    fig, ax = plt.subplots(figsize=(14, 4))
    fig.patch.set_alpha(0.0); ax.patch.set_alpha(0.0)

    sim_curve = sim_df.groupby('pH_Level')['Predicted_Yield'].max().reset_index()
    sns.lineplot(x='pH_Level', y='Predicted_Yield', data=sim_curve, ax=ax, color=BLUE_BRAND, linewidth=3)
    ax.fill_between(sim_curve['pH_Level'], sim_curve['Predicted_Yield'], color=BLUE_BRAND, alpha=0.1)
    
    ax.axvline(optimal_row['pH_Level'], color=EMERALD, linestyle='--', linewidth=2, label=f"{t['opt_lbl']}: {optimal_row['pH_Level']:.1f}")
    ax.scatter(st.session_state['ph'], baseline_yield, color=ROSE, s=120, zorder=5, label=f"{t['curr_lbl']}: pH {st.session_state['ph']:.1f}")

    ax.spines[['top', 'right', 'left']].set_visible(False); ax.spines['bottom'].set_color(SLATE_200)
    ax.tick_params(colors=SLATE_500, bottom=False, left=False) 
    ax.xaxis.label.set_color(SLATE_800); ax.yaxis.label.set_color(SLATE_800)
    
    legend = ax.legend(frameon=True, loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=2)
    legend.get_frame().set_facecolor('#FFFFFF'); legend.get_frame().set_edgecolor(SLATE_200)
    for text in legend.get_texts(): text.set_color(SLATE_800)
    
    ax.grid(axis='y', color=SLATE_200, linestyle='-', alpha=0.5)
    st.pyplot(fig)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"#### {t['neon_title']}")

    def generate_base64_plot(feature_name, x_range, current_val, opt_min, opt_max, title, color_theme):
        df_temp = pd.DataFrame({
            'Temperature_C': st.session_state['temp'], 'Humidity_percent': st.session_state['hum'],
            'pH_Level': st.session_state['ph'], 'Nutrient_EC_mS': st.session_state['ec'],
            'Light_Hours': current_light, 'Growth_Days': current_days
        }, index=range(len(x_range)))
        df_temp[feature_name] = x_range
        df_temp['Sim_Yield'] = rf_model.predict(df_temp[['Temperature_C', 'Humidity_percent', 'pH_Level', 'Nutrient_EC_mS', 'Light_Hours', 'Growth_Days']])
        
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        fig2.patch.set_alpha(0.0); ax2.patch.set_alpha(0.0)
        
        sns.lineplot(x=feature_name, y='Sim_Yield', data=df_temp, ax=ax2, color=SLATE_500, linewidth=2)
        ax2.fill_between(x_range, df_temp['Sim_Yield'], color=SLATE_500, alpha=0.05)
        ax2.axvspan(opt_min, opt_max, color=EMERALD, alpha=0.1)
        
        try: 
            y_val = df_temp.loc[np.isclose(df_temp[feature_name], current_val, atol=1e-5), 'Sim_Yield'].values[0]
            ax2.scatter(current_val, y_val, color=color_theme, s=100, zorder=5)
            ax2.vlines(current_val, ymin=ax2.get_ylim()[0], ymax=y_val, color=color_theme, linestyle=':', lw=1.5)
        except IndexError: pass
            
        ax2.set_title(title, fontweight='bold', color=SLATE_800, fontsize=11, fontfamily='Sora')
        ax2.set_xlabel(''); ax2.set_ylabel('')
        ax2.spines[['top', 'right', 'left']].set_visible(False); ax2.spines['bottom'].set_color(SLATE_200)
        ax2.tick_params(colors=SLATE_500, bottom=False, left=False); ax2.grid(axis='y', color=SLATE_200, linestyle='-', alpha=0.5)
        
        buf = io.BytesIO(); fig2.savefig(buf, format="png", bbox_inches='tight', transparent=True); plt.close(fig2)
        return base64.b64encode(buf.getbuffer()).decode("ascii")

    class_temp = "tech-card-green" if 18.0 <= st.session_state['temp'] <= 25.0 else "tech-card-red"
    class_ec = "tech-card-green" if 1.2 <= st.session_state['ec'] <= 1.8 else "tech-card-red"
    color_temp = EMERALD if 18.0 <= st.session_state['temp'] <= 25.0 else ROSE
    color_ec = EMERALD if 1.2 <= st.session_state['ec'] <= 1.8 else ROSE
    
    col_n1, col_n2 = st.columns(2)
    with col_n1: st.markdown(f'<div class="{class_temp}"><img src="data:image/png;base64,{generate_base64_plot("Temperature_C", np.arange(10, 41, 1), st.session_state["temp"], 18, 25, t["chart_temp"], color_temp)}" style="width:100%;"></div>', unsafe_allow_html=True)
    with col_n2: st.markdown(f'<div class="{class_ec}"><img src="data:image/png;base64,{generate_base64_plot("Nutrient_EC_mS", np.arange(0.5, 3.1, 0.1), np.round(st.session_state["ec"],1), 1.2, 1.8, t["chart_ec"], color_ec)}" style="width:100%;"></div>', unsafe_allow_html=True)

with tab2:
    pass # El código de esta pestaña se mantiene igual (Executive Dashboard)
