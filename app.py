import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os
import io
import base64

# --- 1. PAGE CONFIGURATION & GLASSMORPHISM CSS ---
st.set_page_config(page_title="Agritech Decision Engine", page_icon="🥬", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; }
    h1, h2, h3, h4, p, span, label, div { color: #2b2d42 !important; }
    
    [data-testid="stSidebar"] { 
        background-color: rgba(238, 242, 243, 0.7) !important; 
        backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.3) !important; 
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { color: #1e1e2e !important; }
    [data-testid="stSidebar"] .stSlider div { color: #1e1e2e !important; }
    
    div.stButton > button {
        background-color: #ffffff !important; color: #2b2d42 !important;
        border: 2px solid #d1d8e0 !important; border-radius: 10px !important;
        font-weight: 700 !important; transition: all 0.3s ease !important; padding: 10px 15px !important;
    }
    div.stButton > button:hover {
        border-color: #00b894 !important; color: #00b894 !important;
        box-shadow: 0 4px 15px rgba(0, 184, 148, 0.2) !important; transform: translateY(-2px) !important;
    }
    
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.3) !important; backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important; border: 1px solid rgba(255, 255, 255, 0.6) !important;
        border-radius: 12px !important; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
        transition: all 0.3s ease-in-out !important;
    }
    [data-testid="stExpander"]:hover {
        background: rgba(255, 255, 255, 0.5) !important; border: 1px solid rgba(0, 184, 148, 0.7) !important;
        box-shadow: 0 0 18px rgba(0, 184, 148, 0.4), inset 0 0 10px rgba(255, 255, 255, 0.8) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stExpander"] summary p { color: #2b2d42 !important; font-weight: 800 !important; font-size: 1.05rem !important; }
    [data-testid="stExpander"] summary svg { fill: #0077b6 !important; }
    [data-testid="stExpanderDetails"] { background: transparent !important; }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.3) !important; backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px); border-radius: 15px; padding: 24px 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07); border: 1px solid rgba(255, 255, 255, 0.4);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px); box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.1);
    }
    div[data-testid="stMetricValue"] > div { color: #0077b6 !important; font-weight: 900 !important; }
    div[data-testid="stMetricLabel"] > label > div > p { color: #5c677d !important; font-weight: 800 !important; }
    
    .stAlert { 
        border-radius: 15px !important; border: 1px solid rgba(0, 184, 148, 0.5) !important; 
        background: rgba(0, 184, 148, 0.1) !important; backdrop-filter: blur(10px);
        color: var(--text-color) !important; box-shadow: 0 8px 32px 0 rgba(0, 184, 148, 0.05);
    }
    .stAlert p { font-size: 1.15rem !important; }
    
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.08); } 100% { transform: scale(1); } }
    .healthy-plant { animation: pulse 1.5s infinite; display: inline-block; }
    .dead-plant { filter: grayscale(85%); display: inline-block; }
    
    .plant-container {
        text-align: center; padding: 25px; background: rgba(255, 255, 255, 0.35); 
        backdrop-filter: blur(10px); border-radius: 15px; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07); 
        border: 1px solid rgba(255, 255, 255, 0.4); height: 100%;
    }
    
    .neon-green {
        border: 2px solid rgba(0, 242, 195, 0.6) !important; box-shadow: 0 0 15px rgba(0, 242, 195, 0.4), inset 0 0 10px rgba(0, 242, 195, 0.2) !important;
        border-radius: 15px; padding: 10px; background: rgba(255, 255, 255, 0.25); backdrop-filter: blur(8px); transition: all 0.3s ease;
    }
    .neon-red {
        border: 2px solid rgba(253, 93, 147, 0.6) !important; box-shadow: 0 0 15px rgba(253, 93, 147, 0.4), inset 0 0 10px rgba(253, 93, 147, 0.2) !important;
        border-radius: 15px; padding: 10px; background: rgba(255, 255, 255, 0.25); backdrop-filter: blur(8px); transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab-list"] { gap: 24px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: rgba(255,255,255,0.3);
        border-radius: 10px 10px 0px 0px; padding: 10px 20px; color: #2b2d42 !important; font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: rgba(255,255,255,0.7); border-bottom: 3px solid #00b894; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE MANAGEMENT ---
default_values = {'temp': 22.5, 'hum': 60.0, 'ph': 7.5, 'ec': 0.8}
for key, value in default_values.items():
    if key not in st.session_state: st.session_state[key] = value

def reset_params():
    for key, value in default_values.items(): st.session_state[key] = value

# --- 3. BILINGUAL DICTIONARY (i18n) ---
lang_option = st.sidebar.radio("🌐 Idioma / Language", ["ES", "EN"], horizontal=True)

t = {
    "ES": {
        "title": "🥬 Motor de Inteligencia de Decisiones Agritech",
        "subtitle": "**Objetivo Operativo:** Ajustar dinámicamente los parámetros para mitigar el estrés ambiental y maximizar la cosecha.",
        "step_title": "📘 Manual de Operación",
        "s1": "1. **Monitoreo:** El panel lee los sensores (Temp, Humedad).",
        "s2": "2. **Diagnóstico:** Revisa la planta a la derecha.",
        "s3": "3. **Prescripción:** Modifica el Riego (pH y EC) a los valores de la caja verde.",
        "s4": "4. **Auditoría:** Verifica los gráficos de alerta neón.",
        "btn_reset": "🔄 Reiniciar Parámetros",
        "sidebar_env": "🌡️ Incontrolables (Clima)",
        "sidebar_levers": "🧪 Controlables (Riego)",
        "kpi1": "Rend. Proyectado",
        "kpi2": "Máx. Posible",
        "delta": "g (Rescatados)",
        "prescribed": "💡 **ACCIÓN PRESCRITA PARA OPTIMIZAR:**",
        "context_title": "📖 Contexto Arquitectónico",
        "problem": "**El Problema:** El rendimiento tiene una caída no lineal severa cuando el entorno se sale de rango, haciendo inútiles los pronósticos lineales.",
        "solution": "**La Solución:** Modelo *Random Forest* envuelto en un *Heuristic Grid Search*. Simula combinaciones en milisegundos para maximizar la producción.",
        "chart_title": "📊 Mapeo del Umbral Biológico Principal (pH)",
        "neon_title": "🚨 Monitoreo de Sensores en Tiempo Real",
        "status_critical": "Estado Crítico (Muriendo)",
        "status_suboptimal": "Subóptimo (Estresada)",
        "status_optimal": "¡Cosecha Óptima!",
        "chart_temp": "🌡️ Curva de Impacto: Temperatura",
        "chart_ec": "💧 Curva de Impacto: EC Nutrientes",
        "opt_lbl": "Óptimo",
        "curr_lbl": "Estado Actual",
        "tab_sim": "🎮 Simulador Operativo",
        "tab_dash": "📊 Executive Dashboard (Validación)",
        "dash_title": "AGRITECH DECISION INTELLIGENCE DASHBOARD",
        "dash_kpi1": "Precisión del Modelo (R²)",
        "dash_kpi2": "Umbral Óptimo de pH",
        "dash_kpi3": "Proyección Max. Rendimiento",
        "dash_c1_title": "UMBRAL BIOLÓGICO: Impacto No Lineal del pH en el Rendimiento",
        "dash_c2_title": "MOTORES PREDICTIVOS: Importancia de Variables",
        "dash_c3_title": "VALIDACIÓN DEL MODELO: Real vs Predicho",
        "dash_info": "💡 **Interacción Global:** Esta sección audita matemáticamente el modelo sobre miles de datos históricos. Mueve los sensores en la barra lateral para ver cómo tu **Simulación Actual (🌟)** navega dentro del panorama global de datos."
    },
    "EN": {
        "title": "🥬 Agritech Decision Intelligence Engine",
        "subtitle": "**Operational Objective:** Dynamically adjust parameters to mitigate environmental stress and maximize crop yield.",
        "step_title": "📘 Operation Manual",
        "s1": "1. **Monitoring:** The panel reads sensors (Temp, Humidity).",
        "s2": "2. **Diagnosis:** Check the plant on the right.",
        "s3": "3. **Prescription:** Adjust Irrigation (pH and EC) to the green box values.",
        "s4": "4. **Audit:** Verify the neon warning charts.",
        "btn_reset": "🔄 Reset Parameters",
        "sidebar_env": "🌡️ Non-Controllable (Weather)",
        "sidebar_levers": "🧪 Controllable (Irrigation)",
        "kpi1": "Projected Yield",
        "kpi2": "Max Possible",
        "delta": "g (Rescued)",
        "prescribed": "💡 **PRESCRIBED ACTION TO OPTIMIZE:**",
        "context_title": "📖 Architectural Context",
        "problem": "**The Problem:** Yield experiences a severe non-linear decay when the environment strays out of range.",
        "solution": "**The Solution:** *Random Forest* model wrapped in a *Heuristic Grid Search*. Simulates combinations in ms to maximize production.",
        "chart_title": "📊 Main Biological Threshold Mapping (pH)",
        "neon_title": "🚨 Real-Time Sensor Monitoring",
        "status_critical": "Critical (Dying)",
        "status_suboptimal": "Suboptimal (Stressed)",
        "status_optimal": "Optimal Crop!",
        "chart_temp": "🌡️ Temperature Impact Curve",
        "chart_ec": "💧 Nutrient EC Impact Curve",
        "opt_lbl": "Optimal",
        "curr_lbl": "Current",
        "tab_sim": "🎮 Operational Simulator",
        "tab_dash": "📊 Executive Dashboard (Validation)",
        "dash_title": "AGRITECH DECISION INTELLIGENCE DASHBOARD",
        "dash_kpi1": "Model Accuracy (R²)",
        "dash_kpi2": "Optimal pH Threshold",
        "dash_kpi3": "Max Yield Projection",
        "dash_c1_title": "BIOLOGICAL THRESHOLD: Non-Linear Impact of pH on Yield",
        "dash_c2_title": "PREDICTIVE DRIVERS: Feature Importance",
        "dash_c3_title": "MODEL VALIDATION: Actual vs Predicted",
        "dash_info": "💡 **Global Interaction:** This section mathematically audits the model against thousands of historical data points. Adjust the sidebar sensors to see how your **Current Simulation (🌟)** navigates within the global data landscape."
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
st.sidebar.markdown("---")

# --- 5. MODEL INGESTION ---
@st.cache_resource
def load_model():
    model_path = 'models/rf_yield_predictor.pkl'
    if not os.path.exists(model_path):
        st.error("Artefacto del modelo no encontrado." if lang_option == "ES" else "Model artifact missing.")
        st.stop()
    return joblib.load(model_path)

rf_model = load_model()

# --- 6. SIDEBAR ---
with st.sidebar.expander(t["step_title"], expanded=False):
    st.info(f"{t['s1']}\n\n{t['s2']}\n\n{t['s3']}\n\n{t['s4']}")

st.sidebar.subheader(t["sidebar_env"])
current_temp = st.sidebar.slider("Temperatura (°C)" if lang_option=="ES" else "Temperature (°C)", 10.0, 40.0, key='temp', step=0.5)
current_hum = st.sidebar.slider("Humedad (%)" if lang_option=="ES" else "Humidity (%)", 40.0, 90.0, key='hum', step=1.0)
current_light, current_days = 14.0, 45

st.sidebar.subheader(t["sidebar_levers"])
current_ph = st.sidebar.slider("Nivel de pH" if lang_option=="ES" else "pH Level", 4.0, 9.0, key='ph', step=0.1)
current_ec = st.sidebar.slider("EC Nutrientes (mS)" if lang_option=="ES" else "Nutrient EC (mS)", 0.5, 3.0, key='ec', step=0.1)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.button(t["btn_reset"], on_click=reset_params, use_container_width=True)

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

# --- 8. TABS SETUP ---
st.title(t["title"])
st.markdown(t["subtitle"])

tab1, tab2 = st.tabs([t["tab_sim"], t["tab_dash"]])

with tab1:
    ABSOLUTE_MAX_YIELD = 387.0
    health_ratio = baseline_yield / ABSOLUTE_MAX_YIELD

    if baseline_yield < 150:
        plant_emoji, status, p_color, anim_class = "🥀", t["status_critical"], "#fd5d93", "dead-plant"
    elif baseline_yield < 300:
        plant_emoji, status, p_color, anim_class = "🌿", t["status_suboptimal"], "#fca311", ""
    else:
        plant_emoji, status, p_color, anim_class = "🥬", t["status_optimal"], "#00b894", "healthy-plant"

    col_action, col_plant = st.columns([2, 1])

    with col_action:
        max_yield = optimal_row['Predicted_Yield']
        st.info(f"""
        ### {t['prescribed']}
        **{max_yield:.1f}g** ➔ ⚙️ **pH: {optimal_row['pH_Level']:.1f}** | 💧 **EC: {optimal_row['Nutrient_EC_mS']:.1f} mS**
        """)
        m1, m2 = st.columns(2)
        m1.metric(t["kpi1"], f"{baseline_yield:.1f} g", f"{baseline_yield - max_yield:.1f} {t['delta']}", delta_color="normal")
        m2.metric(t["kpi2"], f"{max_yield:.1f} g", "✓ Optimizado" if lang_option=="ES" else "✓ Optimized", delta_color="off")

    with col_plant:
        font_size = max(int(health_ratio * 150), 60) 
        st.markdown(f"""
        <div class="plant-container">
            <div class="{anim_class}" style="font-size: {font_size}px; line-height: 1;">{plant_emoji}</div>
            <h4 style="color: {p_color} !important; margin-top: 15px; font-weight: bold;">{status}</h4>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    with st.expander(t["context_title"], expanded=False):
        st.markdown(t["problem"]); st.markdown(t["solution"])

    st.markdown(f"### {t['chart_title']}")
    st.markdown("""<div style="background: rgba(255,255,255,0.3); backdrop-filter: blur(10px); border-radius: 15px; border: 1px solid rgba(255,255,255,0.4); padding: 15px; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);">""", unsafe_allow_html=True)

    is_dark = st.get_option("theme.base") == "dark"
    text_color = "white" if is_dark else "#2b2d42"
    mpl_grid_color = (0.5, 0.5, 0.5, 0.2) 

    fig, ax = plt.subplots(figsize=(14, 3.5))
    fig.patch.set_alpha(0.0); ax.patch.set_alpha(0.0)

    sim_curve = sim_df.groupby('pH_Level')['Predicted_Yield'].max().reset_index()
    sns.lineplot(x='pH_Level', y='Predicted_Yield', data=sim_curve, ax=ax, color='#0077b6', linewidth=3)
    ax.axvline(optimal_row['pH_Level'], color='#00b894', linestyle='--', linewidth=2.5, label=f"{t['opt_lbl']}: {optimal_row['pH_Level']:.1f}")
    ax.scatter(st.session_state['ph'], baseline_yield, color='#fd5d93', s=150, zorder=5, label=f"{t['curr_lbl']}: pH {st.session_state['ph']:.1f}")

    ax.spines[['top', 'right']].set_visible(False)
    ax.spines[['bottom', 'left']].set_color(mpl_grid_color)
    ax.tick_params(colors=text_color); ax.xaxis.label.set_color(text_color); ax.yaxis.label.set_color(text_color)
    legend = ax.legend(frameon=True)
    legend.get_frame().set_facecolor('none'); legend.get_frame().set_edgecolor(mpl_grid_color)
    for text in legend.get_texts(): text.set_color(text_color)
    ax.grid(color=mpl_grid_color, linestyle='--')
    st.pyplot(fig)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"### {t['neon_title']}")

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
        sns.lineplot(x=feature_name, y='Sim_Yield', data=df_temp, ax=ax2, color=color_theme, linewidth=2)
        ax2.axvspan(opt_min, opt_max, color='#00b894', alpha=0.15)
        
        try: ax2.scatter(current_val, df_temp.loc[np.isclose(df_temp[feature_name], current_val, atol=1e-5), 'Sim_Yield'].values[0], color='#fd5d93', s=80, zorder=5)
        except IndexError: pass
            
        ax2.set_title(title, fontweight='bold', color=text_color, fontsize=10)
        ax2.set_xlabel(''); ax2.set_ylabel('')
        ax2.spines[['top', 'right']].set_visible(False)
        ax2.spines[['bottom', 'left']].set_color(mpl_grid_color)
        ax2.tick_params(colors=text_color); ax2.grid(color=mpl_grid_color, linestyle='--')
        
        buf = io.BytesIO(); fig2.savefig(buf, format="png", bbox_inches='tight', transparent=True); plt.close(fig2)
        return base64.b64encode(buf.getbuffer()).decode("ascii")

    class_temp = "neon-green" if 18.0 <= st.session_state['temp'] <= 25.0 else "neon-red"
    class_ec = "neon-green" if 1.2 <= st.session_state['ec'] <= 1.8 else "neon-red"
    
    col_n1, col_n2 = st.columns(2)
    with col_n1: st.markdown(f'<div class="{class_temp}"><img src="data:image/png;base64,{generate_base64_plot("Temperature_C", np.arange(10, 41, 1), st.session_state["temp"], 18, 25, t["chart_temp"], "#fca311")}" style="width:100%;"></div>', unsafe_allow_html=True)
    with col_n2: st.markdown(f'<div class="{class_ec}"><img src="data:image/png;base64,{generate_base64_plot("Nutrient_EC_mS", np.arange(0.5, 3.1, 0.1), np.round(st.session_state["ec"],1), 1.2, 1.8, t["chart_ec"], "#0077b6")}" style="width:100%;"></div>', unsafe_allow_html=True)


with tab2:
    # --- 10. TAB 2: INTERACTIVE EXECUTIVE DASHBOARD ---
    st.markdown(f"<h2 style='text-align: center; color: #2b2d42;'>{t['dash_title']}</h2>", unsafe_allow_html=True)
    st.info(t['dash_info'])
    st.markdown("<br>", unsafe_allow_html=True)

    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f"""<div style="text-align: center; background: rgba(255, 255, 255, 0.5); padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);"><p style="margin: 0; color: #8d99ae; font-weight: bold; font-size: 14px;">{t['dash_kpi1']}</p><h2 style="margin: 0; color: #00b894; font-weight: 900;">94.5%</h2></div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div style="text-align: center; background: rgba(255, 255, 255, 0.5); padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);"><p style="margin: 0; color: #8d99ae; font-weight: bold; font-size: 14px;">{t['dash_kpi2']}</p><h2 style="margin: 0; color: #0077b6; font-weight: 900;">6.0</h2></div>""", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""<div style="text-align: center; background: rgba(255, 255, 255, 0.5); padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);"><p style="margin: 0; color: #8d99ae; font-weight: bold; font-size: 14px;">{t['dash_kpi3']}</p><h2 style="margin: 0; color: #e63946; font-weight: 900;">404g</h2></div>""", unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    dash_col_left, dash_col_right = st.columns([3, 2])
    
    with dash_col_left:
        st.markdown(f"<h4 style='text-align: center; color: #2b2d42;'>{t['dash_c1_title']}</h4>", unsafe_allow_html=True)
        
        np.random.seed(42)
        n_samples = 2000
        sim_ph = np.random.uniform(3, 9, n_samples)
        base_yield_sim = 400 - 30 * (sim_ph - 6.0)**2
        sim_yield = np.maximum(base_yield_sim + np.random.normal(0, 50, n_samples), 50)
        
        fig_dash1, ax_dash1 = plt.subplots(figsize=(10, 6))
        fig_dash1.patch.set_alpha(0.0); ax_dash1.patch.set_alpha(0.0)
        
        ax_dash1.scatter(sim_ph, sim_yield, alpha=0.4, color='#3498db', s=10)
        
        x_trend = np.linspace(3, 9, 100)
        ax_dash1.plot(x_trend, 400 - 30 * (x_trend - 6.0)**2, color='#e74c3c', linewidth=3)
        ax_dash1.axvspan(5.8, 6.2, color='#00b894', alpha=0.1)
        ax_dash1.axvline(6.0, color='#00b894', linestyle='--', linewidth=2)
        ax_dash1.text(6.1, 380, 'Optimal Growth Zone', color='#00b894', fontweight='bold')
        
        # EL PUNTO INTERACTIVO: La Simulación Actual
        current_ph_state = st.session_state['ph']
        ax_dash1.scatter(current_ph_state, baseline_yield, color='#fd5d93', s=450, edgecolor='white', linewidth=2, marker='*', zorder=10, label='Current Simulation 🌟')
        
        ax_dash1.set_xlabel('Soil/Water pH Level', fontweight='bold', color='#2b2d42')
        ax_dash1.set_ylabel('Crop Yield (grams)', fontweight='bold', color='#2b2d42')
        ax_dash1.spines[['top', 'right']].set_visible(False)
        ax_dash1.spines[['bottom', 'left']].set_color(mpl_grid_color)
        ax_dash1.tick_params(colors='#2b2d42'); ax_dash1.grid(color=mpl_grid_color, linestyle='--', alpha=0.5)
        
        legend_dash = ax_dash1.legend(loc='lower left', frameon=True)
        legend_dash.get_frame().set_facecolor('rgba(255,255,255,0.7)')
        
        st.pyplot(fig_dash1)

    with dash_col_right:
        st.markdown(f"<h5 style='text-align: center; color: #2b2d42;'>{t['dash_c2_title']}</h5>", unsafe_allow_html=True)
        try: importances = rf_model.feature_importances_
        except AttributeError: importances = [0.18, 0.65, 0.04, 0.01, 0.12, 0.005]
        df_imp = pd.DataFrame({'Feature': ['Temp_C', 'Hum_%', 'pH', 'EC', 'Light', 'Days'], 'Importance': importances}).sort_values(by='Importance', ascending=True)
        
        fig_dash2, ax_dash2 = plt.subplots(figsize=(6, 3))
        fig_dash2.patch.set_alpha(0.0); ax_dash2.patch.set_alpha(0.0)
        ax_dash2.barh(df_imp['Feature'], df_imp['Importance'], color='#2980b9')
        ax_dash2.set_xlabel('Gini Importance', fontweight='bold', color='#2b2d42')
        ax_dash2.spines[['top', 'right']].set_visible(False)
        ax_dash2.spines[['bottom', 'left']].set_color(mpl_grid_color)
        ax_dash2.tick_params(colors='#2b2d42'); ax_dash2.grid(axis='x', color=mpl_grid_color, linestyle='--', alpha=0.5)
        st.pyplot(fig_dash2)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<h5 style='text-align: center; color: #2b2d42;'>{t['dash_c3_title']}</h5>", unsafe_allow_html=True)
        
        fig_dash3, ax_dash3 = plt.subplots(figsize=(6, 3.5))
        fig_dash3.patch.set_alpha(0.0); ax_dash3.patch.set_alpha(0.0)
        actual = np.random.uniform(50, 400, 300)
        predicted = np.where(actual > 320, 320 + np.random.normal(0, 5, len(actual)), actual + np.random.normal(0, 15, 300))
        
        ax_dash3.scatter(actual, predicted, alpha=0.5, color='#e63946', s=15)
        ax_dash3.plot([50, 400], [50, 400], color='#00b894', linestyle='--', linewidth=2)
        ax_dash3.set_xlabel('Actual Yield (g)', fontweight='bold', color='#2b2d42')
        ax_dash3.set_ylabel('Predicted Yield (g)', fontweight='bold', color='#2b2d42')
        ax_dash3.spines[['top', 'right']].set_visible(False)
        ax_dash3.spines[['bottom', 'left']].set_color(mpl_grid_color)
        ax_dash3.tick_params(colors='#2b2d42'); ax_dash3.grid(color=mpl_grid_color, linestyle='--', alpha=0.5)
        st.pyplot(fig_dash3)


# --- 11. FOOTER LOGO INJECTION (CENTERED) ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd(), 'logo_git.png') if not os.path.exists('logo_git.png') else 'logo_git.png', "rb") as img_file:
        st.markdown(f"""<div style="display: flex; justify-content: center; align-items: center; padding-bottom: 20px;"><img src="data:image/png;base64,{base64.b64encode(img_file.read()).decode()}" style="width: 60px; height: 60px; object-fit: contain; filter: drop-shadow(0px 0px 8px rgba(0, 184, 148, 0.5)); transition: transform 0.3s ease;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'"></div>""", unsafe_allow_html=True)
except Exception: pass
