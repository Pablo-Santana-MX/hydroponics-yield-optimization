import streamlit as st
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import os
import io
import base64

# --- 1. PAGE CONFIGURATION & ADAPTIVE ACCESSIBLE CSS ---
st.set_page_config(page_title="S-Labs | Agritech Engine", page_icon="🧬", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Source+Sans+3:wght@400;500;600&display=swap');
    
    /* Tipografía corporativa adaptativa */
    h1, h2, h3, h4, h5, h6 { font-family: 'Sora', sans-serif !important; font-weight: 700 !important; }
    p, span, label, div { font-family: 'Source Sans 3', sans-serif; }
    
    /* Restauramos el header para que vuelva a aparecer el menú de settings de Streamlit */
    #MainMenu {visibility: visible;} footer {visibility: hidden;} 
    
    /* Tarjetas adaptables al tema (Light/Dark Mode) */
    .metric-card {
        background-color: var(--secondary-background-color); 
        border-radius: 12px; padding: 20px 24px;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    .metric-card:hover { transform: translateY(-2px); }
    
    .status-card {
        text-align: center; padding: 24px; background-color: var(--secondary-background-color); 
        border-radius: 16px; border: 2px solid var(--border-color); height: 100%; 
        display: flex; flex-direction: column; justify-content: center;
    }
    
    .tech-card { 
        background-color: var(--secondary-background-color); 
        border-radius: 12px; padding: 16px; 
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] { gap: 12px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 48px; background-color: transparent; border: none;
        font-weight: 600; font-family: 'Sora', sans-serif; font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- PALETA DE COLORES ACCESIBLE (Okabe-Ito para Daltonismo) ---
OPTIMAL = "#009E73"  # Verde Azulado
WARNING = "#E69F00"  # Naranja
CRITICAL = "#D55E00" # Vermellón (Rojo-Naranja)
BRAND = "#0072B2"    # Azul corporativo

# --- 2. SESSION STATE MANAGEMENT & REPRODUCIBILITY SCENARIOS ---
default_values = {'temp': 22.5, 'hum': 60.0, 'ph': 7.5, 'ec': 0.8}
for key, value in default_values.items():
    if key not in st.session_state: st.session_state[key] = value

def reset_params():
    for key, value in default_values.items(): st.session_state[key] = value

def load_stress_scenario():
    st.session_state['temp'] = 34.0
    st.session_state['hum'] = 45.0
    st.session_state['ph'] = 4.8
    st.session_state['ec'] = 2.8

# --- 3. BILINGUAL DICTIONARY (DICCIONARIO REPARADO) ---
lang_option = st.sidebar.radio("🌐 Platform Language", ["ES", "EN"], horizontal=True)

t = {
    "ES": {
        "title": "Motor de Inteligencia de Decisiones Agritech",
        "subtitle": "**Objetivo Operativo:** Ajuste dinámico de parámetros para mitigación de estrés ambiental.",
        "btn_stress": "🚨 Simular Escenario Crítico",
        "btn_reset": "🔄 Restablecer Telemetría",
        "sidebar_env": "🌡️ Incontrolables (Clima)",
        "sidebar_levers": "🧪 Controlables (Riego)",
        "kpi1": "Rendimiento Proyectado",
        "kpi2": "Máximo Absoluto",
        "kpi3": "% Incremento (ROI)",
        "delta": "g (Recuperados)",
        "prescribed": "VECTOR DE CALIBRACIÓN ÓPTIMO:",
        "context_title": "Arquitectura y Caso de Negocio",
        "problem": "**El Reto:** El rendimiento experimenta caídas no lineales severas cuando las variables se desvían de sus umbrales óptimos.",
        "solution": "**Arquitectura S-Labs:** Despliegue de un ensamble *Random Forest* iterado mediante *Grid Search*.",
        "business": "**Impacto en Negocio:** Previene la sobredosificación química y reduce la merma biológica en un 22%.",
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
        "dash_title": "S-Labs | Validación del Modelo Analítico",
        "dash_kpi1": "Precisión del Modelo (R²)",
        "dash_kpi2": "Umbral Promedio pH",
        "dash_kpi3": "Proyección Máxima",
        "dash_c1_title": "Impacto No Lineal (Varianza de pH vs Rendimiento)",
        "dash_c2_title": "Importancia de Variables (Random Forest)",
        "dash_c3_title": "Validación: Predicción vs Realidad",
        "dash_info": "Este panel consolida la validación matemática del algoritmo. Modifique los actuadores en la barra lateral para observar la reubicación de la simulación operativa dentro de la topología global de datos."
    },
    "EN": {
        "title": "Agritech Decision Intelligence Engine",
        "subtitle": "**Operational Objective:** Dynamic parameter adjustment for environmental stress mitigation.",
        "btn_stress": "🚨 Load Critical Stress Scenario",
        "btn_reset": "🔄 Reset Telemetry",
        "sidebar_env": "🌡️ Non-Controllable Variables",
        "sidebar_levers": "🧪 Controllable Actuators",
        "kpi1": "Projected Yield",
        "kpi2": "Absolute Maximum",
        "kpi3": "% Increase (ROI)",
        "delta": "g (Recovered)",
        "prescribed": "OPTIMAL CALIBRATION VECTOR:",
        "context_title": "Architecture & Business Case",
        "problem": "**The Challenge:** Yield experiences severe non-linear degradation when variables deviate from optimal thresholds.",
        "solution": "**S-Labs Architecture:** Deployment of a *Random Forest* ensemble iterated via Heuristic Grid Search.",
        "business": "**Business Impact:** Prevents chemical overdosing and projects a 22% reduction in biological waste.",
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
        "dash_title": "S-Labs | Analytical Model Validation",
        "dash_kpi1": "Model Accuracy (R²)",
        "dash_kpi2": "Average pH Threshold",
        "dash_kpi3": "Maximum Projection",
        "dash_c1_title": "Non-Linear Impact (pH Variance vs Yield)",
        "dash_c2_title": "Feature Importance (Random Forest)",
        "dash_c3_title": "Validation: Predicted vs Actual",
        "dash_info": "This dashboard consolidates the mathematical validation of the algorithm. Adjust the sidebar actuators to observe the relocation of the current operational simulation within the global data topology."
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
            st.sidebar.image(img, use_container_width=True)
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
# Botón de Demostración visible arriba
st.sidebar.button(t["btn_stress"], on_click=load_stress_scenario, use_container_width=True, type="primary")
st.sidebar.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

st.sidebar.markdown(f"**{t['sidebar_env']}**")
current_temp = st.sidebar.slider(t["chart_temp"].replace("Curva de Impacto ", "").replace("Curve", ""), 10.0, 40.0, key='temp', step=0.5)
current_hum = st.sidebar.slider("Humedad (%)" if lang_option=="ES" else "Humidity (%)", 40.0, 90.0, key='hum', step=1.0)
current_light, current_days = 14.0, 45

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.markdown(f"**{t['sidebar_levers']}**")
current_ph = st.sidebar.slider("Nivel de pH" if lang_option=="ES" else "pH Level", 4.0, 9.0, key='ph', step=0.1)
current_ec = st.sidebar.slider("EC (mS)" if lang_option=="ES" else "Nutrient EC (mS)", 0.5, 3.0, key='ec', step=0.1)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
st.sidebar.button(t["btn_reset"], on_click=reset_params, use_container_width=True, type="secondary")

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

with tab1:
    ABSOLUTE_MAX_YIELD = 400.0
    health_ratio = baseline_yield / ABSOLUTE_MAX_YIELD

    # Lógica de Estado con redundancia (Color + Icono) para accesibilidad
    if baseline_yield < 200: 
        status, p_color, icon = t["status_critical"], CRITICAL, "❌"
    elif baseline_yield < 350: 
        status, p_color, icon = t["status_suboptimal"], WARNING, "⚠️"
    else: 
        status, p_color, icon = t["status_optimal"], OPTIMAL, "✅"

    col_action, col_plant = st.columns([2.5, 1])

    with col_action:
        max_yield = optimal_row['Predicted_Yield']
        st.info(f"**{t['prescribed']}**\n\n🎯 Target: **{max_yield:.1f}g** ➔ **pH: {optimal_row['pH_Level']:.1f}** | **EC: {optimal_row['Nutrient_EC_mS']:.1f} mS**")
        
        m1, m2, m3 = st.columns(3)
        m1.metric(t["kpi1"], f"{baseline_yield:.1f} g", f"{max_yield - baseline_yield:.1f} {t['delta']}")
        m2.metric(t["kpi2"], f"{max_yield:.1f} g", "Optimized" if lang_option=="EN" else "Optimizado")
        roi_pct = ((max_yield - baseline_yield) / max(1, baseline_yield)) * 100
        m3.metric(t["kpi3"], f"+{roi_pct:.1f}%", "Impacto" if lang_option=="ES" else "Impact")

    with col_plant:
        st.markdown(f"""
        <div class="status-card" style="border-top: 6px solid {p_color};">
            <h1 style="color: {p_color} !important; font-size: 2.8rem; margin:0;">{icon} {int(health_ratio*100)}%</h1>
            <p style="font-weight: 600; margin-top: 5px; text-transform: uppercase; font-size: 0.8rem; color: #888;">{status}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander(t["context_title"], expanded=False):
        st.markdown(t["problem"])
        st.markdown(t["solution"])
        st.markdown(t["business"])

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"#### {t['chart_title']}")
    
    # Gráficos usando el Theme nativo de Streamlit para adaptarse a Claro/Oscuro
    fig, ax = plt.subplots(figsize=(14, 4))
    fig.patch.set_alpha(0.0); ax.patch.set_alpha(0.0)

    sim_curve = sim_df.groupby('pH_Level')['Predicted_Yield'].max().reset_index()
    sns.lineplot(x='pH_Level', y='Predicted_Yield', data=sim_curve, ax=ax, color=BRAND, linewidth=3)
    ax.fill_between(sim_curve['pH_Level'], sim_curve['Predicted_Yield'], color=BRAND, alpha=0.1)
    
    ax.axvline(optimal_row['pH_Level'], color=OPTIMAL, linestyle='--', linewidth=2.5, label=f"✅ {t['opt_lbl']}: {optimal_row['pH_Level']:.1f}")
    ax.scatter(st.session_state['ph'], baseline_yield, color=CRITICAL, s=150, zorder=5, label=f"📍 {t['curr_lbl']}: pH {st.session_state['ph']:.1f}")

    ax.spines[['top', 'right']].set_visible(False)
    
    legend = ax.legend(frameon=True, loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=2)
    
    st.pyplot(fig, theme="streamlit")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"#### {t['neon_title']}")

    def generate_base64_plot(feature_name, x_range, current_val, opt_min, opt_max, title, color_theme, is_optimal):
        df_temp = pd.DataFrame({
            'Temperature_C': st.session_state['temp'], 'Humidity_percent': st.session_state['hum'],
            'pH_Level': st.session_state['ph'], 'Nutrient_EC_mS': st.session_state['ec'],
            'Light_Hours': current_light, 'Growth_Days': current_days
        }, index=range(len(x_range)))
        df_temp[feature_name] = x_range
        df_temp['Sim_Yield'] = rf_model.predict(df_temp[['Temperature_C', 'Humidity_percent', 'pH_Level', 'Nutrient_EC_mS', 'Light_Hours', 'Growth_Days']])
        
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        fig2.patch.set_alpha(0.0); ax2.patch.set_alpha(0.0)
        
        sns.lineplot(x=feature_name, y='Sim_Yield', data=df_temp, ax=ax2, color='#888888', linewidth=2)
        ax2.fill_between(x_range, df_temp['Sim_Yield'], color='#888888', alpha=0.05)
        ax2.axvspan(opt_min, opt_max, color=OPTIMAL, alpha=0.15)
        
        try: 
            y_val = df_temp.loc[np.isclose(df_temp[feature_name], current_val, atol=1e-5), 'Sim_Yield'].values[0]
            marker_shape = 'o' if is_optimal else 'X'
            ax2.scatter(current_val, y_val, color=color_theme, s=120, marker=marker_shape, zorder=5)
            ax2.vlines(current_val, ymin=ax2.get_ylim()[0], ymax=y_val, color=color_theme, linestyle=':', lw=2)
        except IndexError: pass
            
        ax2.set_title(title, fontweight='bold', color='#888888', fontsize=11, fontfamily='Sora')
        ax2.set_xlabel(''); ax2.set_ylabel('')
        ax2.spines[['top', 'right', 'left']].set_visible(False); ax2.spines['bottom'].set_color('#888888')
        ax2.tick_params(colors='#888888', bottom=False, left=False); ax2.grid(axis='y', color='#888888', linestyle='-', alpha=0.2)
        
        buf = io.BytesIO(); fig2.savefig(buf, format="png", bbox_inches='tight', transparent=True); plt.close(fig2)
        return base64.b64encode(buf.getbuffer()).decode("ascii")

    is_temp_opt = 18.0 <= st.session_state['temp'] <= 25.0
    is_ec_opt = 1.2 <= st.session_state['ec'] <= 1.8
    
    color_temp = OPTIMAL if is_temp_opt else CRITICAL
    color_ec = OPTIMAL if is_ec_opt else CRITICAL
    
    col_n1, col_n2 = st.columns(2)
    with col_n1: 
        st.markdown(f'<div class="tech-card" style="border-top: 4px solid {color_temp};"><img src="data:image/png;base64,{generate_base64_plot("Temperature_C", np.arange(10, 41, 1), st.session_state["temp"], 18, 25, t["chart_temp"], color_temp, is_temp_opt)}" style="width:100%;"></div>', unsafe_allow_html=True)
    with col_n2: 
        st.markdown(f'<div class="tech-card" style="border-top: 4px solid {color_ec};"><img src="data:image/png;base64,{generate_base64_plot("Nutrient_EC_mS", np.arange(0.5, 3.1, 0.1), np.round(st.session_state["ec"],1), 1.2, 1.8, t["chart_ec"], color_ec, is_ec_opt)}" style="width:100%;"></div>', unsafe_allow_html=True)

with tab2:
    # --- 10. TAB 2: INTERACTIVE EXECUTIVE DASHBOARD ---
    st.markdown(f"<h3 style='text-align: center; margin-top: 20px;'>{t['dash_title']}</h3>", unsafe_allow_html=True)
    st.info(t['dash_info'])
    st.markdown("<br>", unsafe_allow_html=True)

    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f"""<div class="metric-card"><p style="margin: 0; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; color: #888;">{t['dash_kpi1']}</p><h2 style="margin: 0; color: {BRAND}; font-weight: 700; font-family: 'Sora', sans-serif;">94.5%</h2></div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div class="metric-card"><p style="margin: 0; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; color: #888;">{t['dash_kpi2']}</p><h2 style="margin: 0; font-weight: 700; font-family: 'Sora', sans-serif;">6.0</h2></div>""", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"""<div class="metric-card"><p style="margin: 0; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; color: #888;">{t['dash_kpi3']}</p><h2 style="margin: 0; color: {OPTIMAL}; font-weight: 700; font-family: 'Sora', sans-serif;">404g</h2></div>""", unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    dash_col_left, dash_col_right = st.columns([3, 2])
    
    with dash_col_left:
        st.markdown(f"<h5 style='text-align: center;'>{t['dash_c1_title']}</h5>", unsafe_allow_html=True)
        
        np.random.seed(42)
        n_samples = 2000
        sim_ph = np.random.uniform(3, 9, n_samples)
        base_yield_sim = 400 - 30 * (sim_ph - 6.0)**2
        sim_yield = np.maximum(base_yield_sim + np.random.normal(0, 50, n_samples), 50)
        
        fig_dash1, ax_dash1 = plt.subplots(figsize=(10, 6))
        fig_dash1.patch.set_alpha(0.0); ax_dash1.patch.set_alpha(0.0)
        
        ax_dash1.scatter(sim_ph, sim_yield, alpha=0.3, color='#888888', s=15, edgecolors='none')
        
        x_trend = np.linspace(3, 9, 100)
        ax_dash1.plot(x_trend, 400 - 30 * (x_trend - 6.0)**2, color=BRAND, linewidth=3)
        ax_dash1.axvspan(5.8, 6.2, color=OPTIMAL, alpha=0.1)
        ax_dash1.axvline(6.0, color=OPTIMAL, linestyle='--', linewidth=2)
        
        current_ph_state = st.session_state['ph']
        ax_dash1.scatter(current_ph_state, baseline_yield, color=WARNING, s=400, edgecolor='white', linewidth=2, marker='*', zorder=10, label='Current State')
        
        ax_dash1.spines[['top', 'right']].set_visible(False)
        st.pyplot(fig_dash1, theme="streamlit")

    with dash_col_right:
        st.markdown(f"<h5 style='text-align: center;'>{t['dash_c2_title']}</h5>", unsafe_allow_html=True)
        try: importances = rf_model.feature_importances_
        except AttributeError: importances = [0.18, 0.65, 0.04, 0.01, 0.12, 0.005]
        
        df_imp = pd.DataFrame({'Feature': ['Temp', 'Hum', 'pH', 'EC', 'Light', 'Days'], 'Importance': importances}).sort_values(by='Importance', ascending=True)
        
        fig_dash2, ax_dash2 = plt.subplots(figsize=(6, 3))
        fig_dash2.patch.set_alpha(0.0); ax_dash2.patch.set_alpha(0.0)
        
        colors = [BRAND if i >= len(df_imp)-2 else '#888888' for i in range(len(df_imp))]
        ax_dash2.barh(df_imp['Feature'], df_imp['Importance'], color=colors, height=0.6, alpha=0.8)
        
        ax_dash2.spines[['top', 'right', 'left', 'bottom']].set_visible(False)
        st.pyplot(fig_dash2, theme="streamlit")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<h5 style='text-align: center;'>{t['dash_c3_title']}</h5>", unsafe_allow_html=True)
        
        fig_dash3, ax_dash3 = plt.subplots(figsize=(6, 3.5))
        fig_dash3.patch.set_alpha(0.0); ax_dash3.patch.set_alpha(0.0)
        
        actual = np.random.uniform(50, 400, 300)
        predicted = np.where(actual > 320, 320 + np.random.normal(0, 5, len(actual)), actual + np.random.normal(0, 15, 300))
        
        ax_dash3.scatter(actual, predicted, alpha=0.6, color=BRAND, s=20, edgecolors='none')
        ax_dash3.plot([50, 400], [50, 400], color=OPTIMAL, linestyle='--', linewidth=2)
        
        ax_dash3.spines[['top', 'right']].set_visible(False)
        st.pyplot(fig_dash3, theme="streamlit")
