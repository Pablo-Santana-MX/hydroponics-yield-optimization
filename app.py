"""
S-Labs | Agritech Decision Intelligence Engine  (v2 · Enterprise refactor)

Requisitos: streamlit>=1.50, numpy, pandas, matplotlib, joblib, pillow (logo)
Opcional  : models/rf_yield_predictor.pkl  -> modelo real (si no existe, usa MockModel)
            data/lettuce_growth_clean.csv  -> hold-out real (FEATURES + Yield_g)
"""
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.figure import Figure
from matplotlib.patches import Patch

# =============================================================================
# 0. CONFIGURACIÓN GLOBAL
# =============================================================================
st.set_page_config(page_title="S-Labs | Agritech Engine", page_icon="🧬", layout="wide")


def _st_version():
    try:
        return tuple(int(p) for p in st.__version__.split(".")[:2])
    except Exception:
        return (0, 0)


STRETCH = {"width": "stretch"} if _st_version() >= (1, 50) else {"use_container_width": True}

FEATURES = ["Temperature_C", "Humidity_percent", "pH_Level", "Nutrient_EC_mS", "Light_Hours", "Growth_Days"]
CONTROLLABLE_IDX = (2, 3)  # pH y EC son las palancas operables

# Paleta Okabe-Ito (apta para daltonismo)
OPTIMAL = "#009E73"   # verde azulado
WARNING = "#E69F00"   # naranja
CRITICAL = "#D55E00"  # vermellón
BRAND = "#0072B2"     # azul corporativo
MUTED = "#7D8590"     # gris neutro: legible en modo claro y oscuro
NEUTRAL_FILL = "#6E7781"

LIGHT_HOURS, GROWTH_DAYS = 14.0, 45
RANGES = {"temp": (10.0, 40.0), "hum": (40.0, 90.0), "ph": (4.0, 9.0), "ec": (0.5, 3.0)}
OPT_ZONES = {"temp": (18.0, 25.0), "ec": (1.2, 1.8)}
PH_AXIS = np.round(np.arange(4.0, 9.05, 0.1), 1)   # dominio de búsqueda = rango operativo del actuador
EC_AXIS = np.round(np.arange(0.5, 3.05, 0.1), 1)
TEMP_AXIS = np.arange(10.0, 40.5, 1.0)

MODEL_PATH = "models/rf_yield_predictor.pkl"
HOLDOUT_PATH = "data/lettuce_growth_clean.csv" # RUTA ACTUALIZADA A TU DATASET

# =============================================================================
# 1. CSS ADAPTATIVO (claro/oscuro) · estética "Clean Tech"
# =============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Source+Sans+3:wght@400;500;600&display=swap');

:root { --sl-border: rgba(128,128,128,.28); --sl-surface: rgba(128,128,128,.07); --sl-muted: #7D8590; }

.stApp { font-family: 'Source Sans 3', sans-serif; }
h1, h2, h3, h4, h5, h6 { font-family: 'Sora', sans-serif !important; font-weight: 700 !important; letter-spacing: -0.02em; }
h1 { font-size: 2.2rem !important; margin-bottom: .2rem !important; padding-bottom: 0 !important; }

.block-container { padding-top: 2.4rem; padding-bottom: 4rem; max-width: 1240px; }
footer { visibility: hidden; }
section[data-testid="stSidebar"] { border-right: 1px solid var(--sl-border); }

/* Jerarquía */
.eyebrow { font: 600 .74rem 'Sora', sans-serif; letter-spacing: .14em; text-transform: uppercase; color: var(--sl-muted); margin-bottom: .4rem; }
.badge { display:inline-block; margin-left: 10px; padding: 2px 10px; border-radius: 999px; border: 1px solid #E69F00; color: #E69F00; font-size: .68rem; letter-spacing: .06em; }
.section-head { margin: 2.4rem 0 .9rem; }
.section-head h4 { margin: 0; font-size: 1.15rem; }
.section-head p { margin: .25rem 0 0; color: var(--sl-muted); font-size: .94rem; }
.card-head { display:flex; align-items:center; justify-content:space-between; gap:10px; flex-wrap:wrap; margin-bottom:.4rem; }
.card-title { font: 600 .98rem 'Sora', sans-serif; }
.chip { display:inline-block; font-size:.78rem; font-weight:600; padding:2px 10px; border-radius:999px; border:1px solid; white-space:nowrap; }

/* Tarjetas KPI */
.kpi { background: var(--sl-surface); border: 1px solid var(--sl-border); border-radius: 14px; padding: 18px 22px; min-height: 118px;
       box-shadow: 0 1px 2px rgba(0,0,0,.06); transition: transform .2s ease, box-shadow .2s ease; }
.kpi:hover { transform: translateY(-2px); box-shadow: 0 8px 18px -8px rgba(0,0,0,.25); }
.kpi-label { font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; font-weight: 600; color: var(--sl-muted); margin-bottom: 6px; }
.kpi-value { font: 700 1.75rem/1.15 'Sora', sans-serif; }
.kpi-sub { font-size: .85rem; color: var(--sl-muted); margin-top: 4px; }

/* Prescripción */
.rx { border-left: 5px solid #0072B2; min-height: 150px; }
.rx-values { display:flex; gap: 40px; flex-wrap: wrap; margin-top: 4px; }
.rx-num { font: 700 1.9rem/1.15 'Sora', sans-serif; }

/* Estado de salud del cultivo */
.status { text-align:center; padding: 22px 16px; background: var(--sl-surface); border: 1px solid var(--sl-border); border-radius: 14px; min-height: 150px;
          display:flex; flex-direction:column; justify-content:center; }
.status-value { font: 700 2.4rem/1.1 'Sora', sans-serif; margin: 2px 0; }
.status-text { font-weight: 600; font-size: .8rem; text-transform: uppercase; letter-spacing: .06em; color: var(--sl-muted); }

/* Takeaways */
.takeaway { border-left: 3px solid #0072B2; background: rgba(0,114,178,.08); padding: 10px 16px; border-radius: 0 10px 10px 0; font-size: .95rem; margin: 8px 0 4px; }
.takeaway.warn { border-left-color: #E69F00; background: rgba(230,159,0,.10); }

/* Pestañas */
.stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid var(--sl-border); }
.stTabs [data-baseweb="tab"] { height: 46px; padding: 0 14px; background: transparent; }
.stTabs [data-baseweb="tab"] p { font-family: 'Sora', sans-serif; font-weight: 600; font-size: .9rem; }

/* Responsivo y accesibilidad */
@media (max-width: 768px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; }
  h1 { font-size: 1.7rem !important; }
  .kpi-value { font-size: 1.4rem; } .rx-num { font-size: 1.5rem; } .rx-values { gap: 20px; }
}
@media (prefers-reduced-motion: reduce) { .kpi { transition: none; } .kpi:hover { transform: none; } }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. DICCIONARIO BILINGÜE
# =============================================================================
TEXT = {
    "ES": {
        "eyebrow": "S-Labs · Decision Intelligence", "badge_demo": "DEMO · Modelo simulado",
        "title": "Motor de Inteligencia de Decisiones Agritech",
        "subtitle": "**Objetivo operativo:** ajuste dinámico de pH y EC para mitigar el estrés ambiental y maximizar el rendimiento por planta.",
        "btn_stress": "🚨 Simular Escenario Crítico", "btn_reset": "🔄 Restablecer Telemetría",
        "sidebar_env": "🌡️ Incontrolables (Clima)", "sidebar_levers": "🧪 Controlables (Riego)",
        "sidebar_biz": "💼 Supuestos de negocio",
        "lbl_temp": "Temperatura (°C)", "lbl_hum": "Humedad (%)", "lbl_ph": "Nivel de pH", "lbl_ec": "EC (mS)",
        "help_temp": "Rango óptimo: 18–25 °C", "help_hum": "Referencia óptima: ~65 %",
        "help_ph": "Referencia óptima: ~6.0", "help_ec": "Rango óptimo: 1.2–1.8 mS",
        "lbl_price": "Precio de venta (USD/kg)", "lbl_plants": "Plantas en producción", "lbl_cycles": "Ciclos por año",
        "tab_sim": "Simulador Operativo", "tab_dash": "Dashboard Ejecutivo (Validación)",
        "prescribed": "VECTOR DE CALIBRACIÓN ÓPTIMO", "target": "Rendimiento objetivo", "adjust": "Ajuste requerido",
        "health_lbl": "Índice de salud del cultivo",
        "status_critical": "Pérdida Operativa Crítica", "status_suboptimal": "Estrés Biológico Detectado", "status_optimal": "Rendimiento Maximizado",
        "sec_yield": "Rendimiento por planta", "sec_yield_cap": "Telemetría actual vs. potencial con la calibración prescrita.",
        "kpi1": "Rendimiento proyectado", "kpi2": "Potencial con calibración", "kpi3": "Incremento de rendimiento",
        "delta": "g recuperables", "optimized": "Con el vector óptimo", "impact": "vs. telemetría actual",
        "sec_fin": "Impacto financiero", "sec_fin_cap": "Calculado con los supuestos de negocio de la barra lateral (por ciclo de cultivo).",
        "fin1": "Ingreso por ciclo · hoy", "fin2": "Ingreso por ciclo · calibrado", "fin3": "Valor recuperable por ciclo", "fin4": "Impacto anualizado",
        "fin1_sub": "Con la telemetría actual", "fin2_sub": "Con pH y EC óptimos", "fin3_sub": "{pct:.0f}% sobre el ingreso actual", "fin4_sub": "{cycles} ciclos al año",
        "seg_captured": "Capturado hoy", "seg_recover": "Recuperable con calibración", "seg_residual": "Limitado por clima",
        "fin_take": "La calibración recupera <b>{rec}</b> por ciclo (<b>{ann}</b> al año) y cierra el <b>{closed:.0f}%</b> de la brecha frente al máximo teórico. Los <b>{res}</b> restantes dependen del clima y no se corrigen con riego.",
        "fin_take_ok": "La operación ya está en el punto óptimo de calibración. La brecha restante (<b>{res}</b> por ciclo) es atribuible al clima.",
        "takeaway_lbl": "Takeaway:",
        "context_title": "Arquitectura y Caso de Negocio",
        "problem": "**El Reto:** El rendimiento experimenta caídas no lineales severas cuando las variables se desvían de sus umbrales óptimos.",
        "solution": "**Arquitectura S-Labs:** Despliegue de un ensamble *Random Forest* iterado mediante *Grid Search* sobre el rango operativo de los actuadores (pH y EC).",
        "business": "**Impacto en Negocio:** Previene la sobredosificación química y reduce la merma biológica: con la telemetría actual, la calibración cierra el {closed:.0f}% de la brecha de rendimiento.",
        "chart_title": "Mapeo de Umbral Biológico Principal (pH)", "chart_cap": "Rendimiento esperado según pH, con la EC actual y con la mejor EC posible.",
        "line_current_ec": "Con EC actual", "line_best_ec": "Con la mejor EC", "opt_lbl": "Vector óptimo", "curr_lbl": "Telemetría actual",
        "ph_take": "Llevar el pH de <b>{cur_ph:.1f}</b> a <b>{best_ph:.1f}</b> y la EC de <b>{cur_ec:.1f}</b> a <b>{best_ec:.1f} mS</b> eleva el rendimiento de <b>{base:.0f} g</b> a <b>{best:.0f} g</b> por planta.",
        "ph_take_ok": "La telemetría actual coincide con el vector óptimo: no se requieren ajustes.",
        "neon_title": "Auditoría de Sensibilidad de Sensores", "neon_cap": "Cómo cambia el rendimiento al mover una sola variable, manteniendo las demás en su valor actual.",
        "chart_temp": "Curva de Impacto Térmico", "chart_ec": "Curva de Impacto Nutricional (EC)",
        "in_range": "Dentro del rango óptimo ({rng})", "out_range": "Fuera del rango óptimo ({rng})", "zone_lbl": "zona óptima",
        "ax_yield": "Rendimiento (g)", "ax_ph": "Nivel de pH",
        "dash_title": "Validación del Modelo Analítico",
        "dash_info": "Consolida la validación del algoritmo. Modifique los actuadores en la barra lateral para ver cómo se reubica la operación actual dentro de la topología global de datos.",
        "dash_demo_note": "Datos de validación sintéticos. Para validación real, su archivo se cargará desde data/lettuce_growth_clean.csv.",
        "dash_kpi1": "Precisión del modelo (R²)", "dash_kpi1_sub": "Hold-out sintético (demo)", "dash_kpi1_sub_real": "Hold-out real",
        "dash_kpi2": "Error medio (MAE)", "dash_kpi2_sub": "gramos por planta",
        "dash_kpi3": "pH óptimo global", "dash_kpi3_sub": "Máximo del modelo",
        "dash_kpi4": "Techo de rendimiento", "dash_kpi4_sub": "Con condiciones ideales",
        "dash_c1_title": "1 · El problema: la pérdida de valor es no lineal", "dash_c2_title": "2 · La palanca: qué variables mueven el rendimiento", "dash_c3_title": "3 · La confianza: predicción vs. realidad",
        "dash_c1_take": "Fuera de ±0.5 unidades de pH respecto al óptimo (<b>{opt:.1f}</b>), el rendimiento mediano cae <b>{loss:.0f}%</b> ({med_out:.0f} g vs. {med_in:.0f} g).",
        "dash_c2_take": "pH y EC concentran el <b>{share:.0%}</b> de la capacidad predictiva del modelo: son palancas que el operador puede ajustar hoy.",
        "dash_c3_take": "Error medio de <b>{mae:.1f} g</b> por planta (R² = <b>{r2:.2f}</b>): cuanto más cerca de la diagonal, más confiable es la prescripción.",
        "lbl_ops": "Operaciones históricas", "lbl_median": "Mediana por rango de pH", "lbl_iqr": "Rango intercuartil", "lbl_zone": "Zona óptima (±0.5)", "lbl_state": "Estado actual",
        "feat_names": ["Temperatura", "Humedad", "pH", "EC", "Luz", "Días"], "lbl_controllable": "Controlable", "lbl_uncontrollable": "No controlable",
        "ax_actual": "Rendimiento real (g)", "ax_pred": "Rendimiento predicho (g)",
        "footer": "S-Labs · Advanced Data Solutions — Demo con modelo y datos simulados; los resultados ilustran la metodología, no una garantía de rendimiento.",
    },
    "EN": {
        "eyebrow": "S-Labs · Decision Intelligence", "badge_demo": "DEMO · Simulated model",
        "title": "Agritech Decision Intelligence Engine",
        "subtitle": "**Operational objective:** dynamic pH and EC adjustment to mitigate environmental stress and maximize yield per plant.",
        "btn_stress": "🚨 Load Critical Stress Scenario", "btn_reset": "🔄 Reset Telemetry",
        "sidebar_env": "🌡️ Non-Controllable Variables", "sidebar_levers": "🧪 Controllable Actuators",
        "sidebar_biz": "💼 Business assumptions",
        "lbl_temp": "Temperature (°C)", "lbl_hum": "Humidity (%)", "lbl_ph": "pH Level", "lbl_ec": "Nutrient EC (mS)",
        "help_temp": "Optimal range: 18–25 °C", "help_hum": "Optimal reference: ~65 %",
        "help_ph": "Optimal reference: ~6.0", "help_ec": "Optimal range: 1.2–1.8 mS",
        "lbl_price": "Selling price (USD/kg)", "lbl_plants": "Plants in production", "lbl_cycles": "Cycles per year",
        "tab_sim": "Operational Simulator", "tab_dash": "Executive Dashboard (Validation)",
        "prescribed": "OPTIMAL CALIBRATION VECTOR", "target": "Target yield", "adjust": "Required adjustment",
        "health_lbl": "Crop health index",
        "status_critical": "Critical Operational Loss", "status_suboptimal": "Biological Stress Detected", "status_optimal": "Yield Maximized",
        "sec_yield": "Yield per plant", "sec_yield_cap": "Current telemetry vs. potential under the prescribed calibration.",
        "kpi1": "Projected yield", "kpi2": "Potential with calibration", "kpi3": "Yield increase",
        "delta": "g recoverable", "optimized": "With the optimal vector", "impact": "vs. current telemetry",
        "sec_fin": "Financial impact", "sec_fin_cap": "Computed from the business assumptions in the sidebar (per crop cycle).",
        "fin1": "Revenue per cycle · today", "fin2": "Revenue per cycle · calibrated", "fin3": "Recoverable value per cycle", "fin4": "Annualized impact",
        "fin1_sub": "At current telemetry", "fin2_sub": "At optimal pH and EC", "fin3_sub": "{pct:.0f}% over current revenue", "fin4_sub": "{cycles} cycles per year",
        "seg_captured": "Captured today", "seg_recover": "Recoverable via calibration", "seg_residual": "Climate-limited",
        "fin_take": "Calibration recovers <b>{rec}</b> per cycle (<b>{ann}</b> per year), closing <b>{closed:.0f}%</b> of the gap to the theoretical maximum. The remaining <b>{res}</b> is climate-bound and cannot be fixed through irrigation.",
        "fin_take_ok": "Operations are already at the optimal calibration point. The remaining gap (<b>{res}</b> per cycle) is attributable to climate.",
        "takeaway_lbl": "Takeaway:",
        "context_title": "Architecture & Business Case",
        "problem": "**The Challenge:** Yield experiences severe non-linear degradation when variables deviate from optimal thresholds.",
        "solution": "**S-Labs Architecture:** Deployment of a *Random Forest* ensemble iterated via *Grid Search* over the actuators' operating range (pH and EC).",
        "business": "**Business Impact:** Prevents chemical overdosing and reduces biological waste: at current telemetry, calibration closes {closed:.0f}% of the yield gap.",
        "chart_title": "Primary Biological Threshold Mapping (pH)", "chart_cap": "Expected yield by pH, at the current EC and at the best possible EC.",
        "line_current_ec": "At current EC", "line_best_ec": "At best EC", "opt_lbl": "Optimal vector", "curr_lbl": "Current telemetry",
        "ph_take": "Moving pH from <b>{cur_ph:.1f}</b> to <b>{best_ph:.1f}</b> and EC from <b>{cur_ec:.1f}</b> to <b>{best_ec:.1f} mS</b> lifts yield from <b>{base:.0f} g</b> to <b>{best:.0f} g</b> per plant.",
        "ph_take_ok": "Current telemetry matches the optimal vector: no adjustment required.",
        "neon_title": "Sensor Sensitivity Audit", "neon_cap": "How yield changes when moving a single variable while holding the others at their current value.",
        "chart_temp": "Thermal Impact Curve", "chart_ec": "Nutritional Impact Curve (EC)",
        "in_range": "Within optimal range ({rng})", "out_range": "Outside optimal range ({rng})", "zone_lbl": "optimal zone",
        "ax_yield": "Yield (g)", "ax_ph": "pH Level",
        "dash_title": "Analytical Model Validation",
        "dash_info": "Consolidates the algorithm's validation. Adjust the sidebar actuators to see how the current operation relocates within the global data topology.",
        "dash_demo_note": "Synthetic validation data. For real validation, drop your file into data/lettuce_growth_clean.csv.",
        "dash_kpi1": "Model accuracy (R²)", "dash_kpi1_sub": "Synthetic hold-out (demo)", "dash_kpi1_sub_real": "Real hold-out",
        "dash_kpi2": "Mean absolute error", "dash_kpi2_sub": "grams per plant",
        "dash_kpi3": "Global optimal pH", "dash_kpi3_sub": "Model maximum",
        "dash_kpi4": "Yield ceiling", "dash_kpi4_sub": "Under ideal conditions",
        "dash_c1_title": "1 · The problem: value loss is non-linear", "dash_c2_title": "2 · The lever: which variables move yield", "dash_c3_title": "3 · The trust: predicted vs. actual",
        "dash_c1_take": "Beyond ±0.5 pH units from the optimum (<b>{opt:.1f}</b>), median yield drops <b>{loss:.0f}%</b> ({med_out:.0f} g vs. {med_in:.0f} g).",
        "dash_c2_take": "pH and EC account for <b>{share:.0%}</b> of the model's predictive power: levers the operator can adjust today.",
        "dash_c3_take": "Mean error of <b>{mae:.1f} g</b> per plant (R² = <b>{r2:.2f}</b>): the closer to the diagonal, the more reliable the prescription.",
        "lbl_ops": "Historical operations", "lbl_median": "Median by pH bin", "lbl_iqr": "Interquartile range", "lbl_zone": "Optimal zone (±0.5)", "lbl_state": "Current state",
        "feat_names": ["Temperature", "Humidity", "pH", "EC", "Light", "Days"], "lbl_controllable": "Controllable", "lbl_uncontrollable": "Non-controllable",
        "ax_actual": "Actual yield (g)", "ax_pred": "Predicted yield (g)",
        "footer": "S-Labs · Advanced Data Solutions — Demo using a simulated model and data; results illustrate the methodology, not a performance guarantee.",
    },
}

# =============================================================================
# 3. ESTADO DE SESIÓN
# =============================================================================
TELEMETRY_DEFAULTS = {"temp": 22.5, "hum": 60.0, "ph": 7.5, "ec": 0.8}
BUSINESS_DEFAULTS = {"price_kg": 6.0, "plants": 10000, "cycles": 6}
for _k, _v in {**TELEMETRY_DEFAULTS, **BUSINESS_DEFAULTS}.items():
    st.session_state.setdefault(_k, _v)


def reset_params():
    for k, v in TELEMETRY_DEFAULTS.items():
        st.session_state[k] = v


def load_stress_scenario():
    st.session_state.update({"temp": 34.0, "hum": 45.0, "ph": 4.8, "ec": 2.8})


# =============================================================================
# 4. MODELO (mock vectorizado + carga del modelo real si existe)
# =============================================================================
def build_frame(temp, hum, ph, ec):
    arrs = np.broadcast_arrays(*[np.atleast_1d(np.asarray(v, dtype=float)) for v in (temp, hum, ph, ec)])
    return pd.DataFrame({
        "Temperature_C": arrs[0], "Humidity_percent": arrs[1], "pH_Level": arrs[2], "Nutrient_EC_mS": arrs[3],
        "Light_Hours": LIGHT_HOURS, "Growth_Days": GROWTH_DAYS,
    })[FEATURES]


class MockModel:
    feature_importances_ = np.array([0.18, 0.05, 0.45, 0.20, 0.10, 0.02])

    def predict(self, X):
        X = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X, columns=FEATURES)
        y = (400.0
             - 0.9 * (X["Temperature_C"].to_numpy(float) - 22.0) ** 2
             - 0.12 * (X["Humidity_percent"].to_numpy(float) - 65.0) ** 2
             - 40.0 * (X["pH_Level"].to_numpy(float) - 6.0) ** 2
             - 50.0 * (X["Nutrient_EC_mS"].to_numpy(float) - 1.5) ** 2)
        return np.maximum(50.0, y)


@st.cache_resource(show_spinner=False)
def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH), False
    return MockModel(), True


def get_importances(model):
    imp = getattr(model, "feature_importances_", None)
    if imp is None or len(imp) != len(FEATURES):
        imp = MockModel.feature_importances_
    return np.asarray(imp, dtype=float)


# =============================================================================
# 5. MOTOR DE OPTIMIZACIÓN Y VALIDACIÓN (ACTUALIZADO PARA Yield_g)
# =============================================================================
@st.cache_data(show_spinner=False)
def optimize(_model, temp, hum, ph, ec):
    baseline = float(_model.predict(build_frame(temp, hum, ph, ec))[0])
    gp, ge = np.meshgrid(PH_AXIS, EC_AXIS)
    yields = np.asarray(_model.predict(build_frame(temp, hum, gp.ravel(), ge.ravel())), dtype=float).reshape(gp.shape)
    i_ec, i_ph = np.unravel_index(yields.argmax(), yields.shape)
    return {
        "baseline": baseline, "best_yield": float(yields[i_ec, i_ph]),
        "best_ph": float(PH_AXIS[i_ph]), "best_ec": float(EC_AXIS[i_ec]),
        "curve_best_ec": yields.max(axis=0),
        "curve_current_ec": np.asarray(_model.predict(build_frame(temp, hum, PH_AXIS, ec)), dtype=float),
    }


@st.cache_data(show_spinner=False)
def global_optimum(_model):
    g = np.meshgrid(TEMP_AXIS, np.arange(40.0, 90.5, 5.0), np.linspace(4, 9, 21), np.linspace(0.5, 3.0, 11), indexing="ij")
    X = build_frame(*[a.ravel() for a in g])
    y = np.asarray(_model.predict(X), dtype=float)
    i = int(np.argmax(y))
    return {"ceiling": float(y[i]), "ph": float(X["pH_Level"].iloc[i]), "ec": float(X["Nutrient_EC_mS"].iloc[i])}


@st.cache_data(show_spinner=False)
def sensitivity(_model, feature, axis, temp, hum, ph, ec):
    v = {"temp": temp, "hum": hum, "ph": ph, "ec": ec}
    v[feature] = axis
    return np.asarray(_model.predict(build_frame(**v)), dtype=float)


@st.cache_data(show_spinner=False)
def validation_set(_model):
    if os.path.exists(HOLDOUT_PATH):
        try:
            df = pd.read_csv(HOLDOUT_PATH)
            if set(FEATURES + ["Yield_g"]).issubset(df.columns):
                return df[FEATURES].copy(), df["Yield_g"].to_numpy(float), np.asarray(_model.predict(df[FEATURES]), float), False
        except Exception:
            pass
    rng = np.random.default_rng(42)
    n = 2000
    X = build_frame(np.clip(rng.normal(24, 6, n), *RANGES["temp"]), np.clip(rng.normal(65, 12, n), *RANGES["hum"]),
                    np.clip(rng.normal(6.2, 1.0, n), *RANGES["ph"]), np.clip(rng.normal(1.6, 0.5, n), *RANGES["ec"]))
    pred = np.asarray(_model.predict(X), dtype=float)
    actual = np.maximum(50.0, pred + rng.normal(0, 15, n))
    return X, actual, pred, True


# =============================================================================
# 6. HELPERS DE UI Y GRÁFICOS
# =============================================================================
def usd(v):
    a = abs(v)
    if a >= 1e6:
        return f"${v / 1e6:,.2f}M"
    if a >= 1e4:
        return f"${v / 1e3:,.1f}k"
    return f"${v:,.0f}"


def spacer(rem=1.0):
    st.markdown(f'<div style="height:{rem}rem"></div>', unsafe_allow_html=True)


def section(title, caption=""):
    cap = f"<p>{caption}</p>" if caption else ""
    st.markdown(f'<div class="section-head"><h4>{title}</h4>{cap}</div>', unsafe_allow_html=True)


def kpi(label, value, sub="", color=None):
    style = f' style="color:{color};"' if color else ""
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value"{style}>{value}</div>{sub_html}</div>',
                unsafe_allow_html=True)


def takeaway(text, warn=False):
    cls = "takeaway warn" if warn else "takeaway"
    lbl = "" if warn else f"<b>{t['takeaway_lbl']}</b> "
    st.markdown(f'<div class="{cls}">{lbl}{text}</div>', unsafe_allow_html=True)


def chip(text, color):
    return f'<span class="chip" style="color:{color};border-color:{color};">{text}</span>'


def new_fig(w, h):
    fig = Figure(figsize=(w, h), dpi=130)
    fig.patch.set_alpha(0.0)
    ax = fig.subplots()
    ax.patch.set_alpha(0.0)
    return fig, ax


def style_ax(ax, xlabel="", ylabel="", grid_axis="y"):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(MUTED)
    ax.spines["bottom"].set_alpha(0.5)
    ax.tick_params(colors=MUTED, labelsize=9, length=0)
    ax.set_xlabel(xlabel, color=MUTED, fontsize=9.5, labelpad=8)
    ax.set_ylabel(ylabel, color=MUTED, fontsize=9.5, labelpad=8)
    ax.grid(axis=grid_axis, color=MUTED, alpha=0.18, lw=0.8)
    ax.set_axisbelow(True)


def legend_below(ax, ncol, handles=None, y=-0.2):
    leg = ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, y), ncol=ncol, frameon=False, fontsize=9,
                    handletextpad=0.5, columnspacing=1.6)
    for txt in leg.get_texts():
        txt.set_color(MUTED)


def show(fig):
    fig.tight_layout(pad=1.0)
    st.pyplot(fig, transparent=True, **STRETCH)


def chart_value_bar(captured, recover, residual):
    total = max(captured + recover + residual, 1e-9)
    fig, ax = new_fig(11, 1.9)
    items = [(captured, BRAND, None, t["seg_captured"]), (recover, OPTIMAL, None, t["seg_recover"]),
             (residual, NEUTRAL_FILL, "///", t["seg_residual"])]
    handles, left = [], 0.0
    for val, color, hatch, label in items:
        if val > 0:
            ax.barh(0, val, left=left, height=0.55, color=color, hatch=hatch,
                    edgecolor=(1, 1, 1, 0.5) if hatch else color, linewidth=0)
            if val / total >= 0.10:
                ax.text(left + val / 2, 0, f"{val / total:.0%}", ha="center", va="center", color="white", fontweight="bold", fontsize=11)
        handles.append(Patch(facecolor=color, hatch=hatch, edgecolor=(1, 1, 1, 0.5) if hatch else color, label=f"{label} · {usd(val)}"))
        left += val
    ax.set_xlim(0, total)
    ax.set_ylim(-0.5, 0.5)
    ax.axis("off")
    legend_below(ax, 3, handles=handles, y=0.02)
    return fig


def chart_ph_response(res, cur_ph):
    fig, ax = new_fig(11, 3.9)
    ax.plot(PH_AXIS, res["curve_current_ec"], color=MUTED, lw=2, label=t["line_current_ec"])
    ax.plot(PH_AXIS, res["curve_best_ec"], color=BRAND, lw=3, label=t["line_best_ec"])
    ax.fill_between(PH_AXIS, res["curve_best_ec"], color=BRAND, alpha=0.08, lw=0)
    ax.axvline(res["best_ph"], color=OPTIMAL, ls="--", lw=2)
    ax.scatter([res["best_ph"]], [res["best_yield"]], marker="*", s=280, color=OPTIMAL, edgecolor="white", linewidth=1.2, zorder=6,
               label=f"{t['opt_lbl']}: pH {res['best_ph']:.1f}")
    ax.scatter([cur_ph], [res["baseline"]], marker="X", s=150, color=CRITICAL, edgecolor="white", linewidth=1.2, zorder=6,
               label=f"{t['curr_lbl']}: pH {cur_ph:.1f}")
    gap = res["best_yield"] - res["baseline"]
    if gap > 1:
        ax.annotate("", xy=(res["best_ph"], res["best_yield"]), xytext=(cur_ph, res["baseline"]),
                    arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.4, ls=":", shrinkA=10, shrinkB=12, connectionstyle="arc3,rad=-0.2"))
        ax.text((cur_ph + res["best_ph"]) / 2, (res["baseline"] + res["best_yield"]) / 2 + 22, f"+{gap:.0f} g",
                ha="center", color=OPTIMAL, fontweight="bold", fontsize=10.5)
    ax.set_xlim(PH_AXIS[0], PH_AXIS[-1])
    ax.set_ylim(0, max(res["best_yield"], res["baseline"]) * 1.15)
    style_ax(ax, t["ax_ph"], t["ax_yield"])
    legend_below(ax, 4)
    return fig


def chart_sensitivity(axis, yields, current, zone, in_zone, xlabel):
    color = OPTIMAL if in_zone else CRITICAL
    fig, ax = new_fig(6, 3.0)
    ymax = max(float(yields.max()), 1.0) * 1.15
    ax.plot(axis, yields, color=MUTED, lw=2.2)
    ax.fill_between(axis, yields, color=MUTED, alpha=0.07, lw=0)
    ax.axvspan(*zone, color=OPTIMAL, alpha=0.14, lw=0)
    ax.text(sum(zone) / 2, ymax * 0.97, t["zone_lbl"], ha="center", va="top", color=MUTED, fontsize=8.5)
    y_cur = float(np.interp(current, axis, yields))
    ax.vlines(current, 0, y_cur, color=color, ls=":", lw=1.8)
    ax.scatter([current], [y_cur], s=120, color=color, marker="o" if in_zone else "X", edgecolor="white", linewidth=1.2, zorder=5)
    ax.set_xlim(axis[0], axis[-1])
    ax.set_ylim(0, ymax)
    style_ax(ax, xlabel, t["ax_yield"])
    return fig


def chart_ph_cloud(ph_vals, actual, opt_ph, cur_ph, cur_yield):
    fig, ax = new_fig(11, 4.2)
    ax.scatter(ph_vals, actual, s=10, color=MUTED, alpha=0.28, linewidths=0, label=t["lbl_ops"])
    bins = np.arange(4.0, 9.01, 0.5)
    idx = np.digitize(ph_vals, bins) - 1
    xs, med, q1, q3 = [], [], [], []
    for b in range(len(bins) - 1):
        m = idx == b
        if m.sum() >= 15:
            v = actual[m]
            xs.append((bins[b] + bins[b + 1]) / 2)
            med.append(np.median(v))
            q1.append(np.percentile(v, 25))
            q3.append(np.percentile(v, 75))
    if xs:
        ax.fill_between(xs, q1, q3, color=BRAND, alpha=0.16, lw=0, label=t["lbl_iqr"])
        ax.plot(xs, med, color=BRAND, lw=3, marker="o", ms=5, label=t["lbl_median"])
    ax.axvspan(opt_ph - 0.5, opt_ph + 0.5, color=OPTIMAL, alpha=0.12, lw=0, label=t["lbl_zone"])
    ax.axvline(opt_ph, color=OPTIMAL, ls="--", lw=2)
    ax.scatter([cur_ph], [cur_yield], marker="*", s=380, color=WARNING, edgecolor="white", linewidth=1.5, zorder=8, label=t["lbl_state"])
    ax.set_xlim(4, 9)
    ax.set_ylim(0, max(float(actual.max()), cur_yield) * 1.1)
    style_ax(ax, t["ax_ph"], t["ax_yield"])
    legend_below(ax, 5)
    return fig


def chart_importance(importances):
    imp = importances / importances.sum()
    order = np.argsort(imp)
    names = t["feat_names"]
    fig, ax = new_fig(6, 3.6)
    colors = [BRAND if i in CONTROLLABLE_IDX else "#9AA4AF" for i in order]
    bars = ax.barh([names[i] for i in order], imp[order], color=colors, height=0.62)
    ax.bar_label(bars, labels=[f"{imp[i]:.0%}" for i in order], padding=6, color=MUTED, fontsize=9.5, fontweight="bold")
    ax.set_xlim(0, imp.max() * 1.22)
    ax.set_xticks([])
    style_ax(ax, grid_axis="x")
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", labelsize=10)
    legend_below(ax, 2, handles=[Patch(color=BRAND, label=t["lbl_controllable"]), Patch(color="#9AA4AF", label=t["lbl_uncontrollable"])], y=-0.08)
    return fig


def chart_pred_actual(actual, pred, r2, mae):
    lo, hi = float(min(actual.min(), pred.min())), float(max(actual.max(), pred.max()))
    pad = (hi - lo) * 0.04
    fig, ax = new_fig(6, 3.6)
    ax.scatter(actual, pred, s=14, color=BRAND, alpha=0.35, linewidths=0)
    ax.plot([lo, hi], [lo, hi], color=OPTIMAL, ls="--", lw=2)
    ax.set_xlim(lo - pad, hi + pad)
    ax.set_ylim(lo - pad, hi + pad)
    ax.text(0.04, 0.95, f"R² = {r2:.3f}\nMAE = {mae:.1f} g", transform=ax.transAxes, va="top", color=MUTED, fontsize=10, fontweight="bold")
    style_ax(ax, t["ax_actual"], t["ax_pred"], grid_axis="both")
    return fig


# =============================================================================
# 7. SIDEBAR
# =============================================================================
lang = st.sidebar.radio("🌐 Platform Language", ["ES", "EN"], horizontal=True)
t = TEXT[lang]


def display_logo(filename):
    base = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    path = base / filename
    if not path.exists() and Path(filename).exists():
        path = Path(filename)
    if path.exists():
        try:
            from PIL import Image
            st.sidebar.image(Image.open(path).convert("RGBA"), **STRETCH)
        except Exception:
            pass


display_logo("logo_git.png")
st.sidebar.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

st.sidebar.button(t["btn_stress"], on_click=load_stress_scenario, type="primary", **STRETCH)
st.sidebar.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

st.sidebar.markdown(f"**{t['sidebar_env']}**")
temp = st.sidebar.slider(t["lbl_temp"], *RANGES["temp"], key="temp", step=0.5, help=t["help_temp"])
hum = st.sidebar.slider(t["lbl_hum"], *RANGES["hum"], key="hum", step=1.0, help=t["help_hum"])

st.sidebar.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
st.sidebar.markdown(f"**{t['sidebar_levers']}**")
ph = st.sidebar.slider(t["lbl_ph"], *RANGES["ph"], key="ph", step=0.1, help=t["help_ph"])
ec = st.sidebar.slider(t["lbl_ec"], *RANGES["ec"], key="ec", step=0.1, help=t["help_ec"])

st.sidebar.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
st.sidebar.button(t["btn_reset"], on_click=reset_params, type="secondary", **STRETCH)

with st.sidebar.expander(t["sidebar_biz"], expanded=False):
    price_kg = st.number_input(t["lbl_price"], min_value=0.1, step=0.5, key="price_kg")
    plants = st.number_input(t["lbl_plants"], min_value=100, step=500, key="plants")
    cycles = st.number_input(t["lbl_cycles"], min_value=1, max_value=12, step=1, key="cycles")

# =============================================================================
# 8. CÁLCULOS DE LA VISTA
# =============================================================================
model, is_mock = load_model()
res = optimize(model, float(temp), float(hum), float(ph), float(ec))
glob = global_optimum(model)

baseline, best = res["baseline"], res["best_yield"]
ceiling = max(glob["ceiling"], best, baseline)
recoverable_g = max(0.0, best - baseline)
gap_total = ceiling - baseline
gap_closed = 1.0 if gap_total <= 1e-9 else min(1.0, recoverable_g / gap_total)
health = baseline / ceiling if ceiling > 0 else 0.0
uplift_pct = recoverable_g / max(1.0, baseline) * 100

rev = lambda grams: grams * plants * price_kg / 1000.0  
rev_now, rev_opt, rev_ceiling = rev(baseline), rev(max(best, baseline)), rev(ceiling)
rev_recover = rev_opt - rev_now
rev_residual = max(0.0, rev_ceiling - rev_opt)
rev_annual = rev_recover * cycles

if health < 0.50:
    status, s_color, s_icon = t["status_critical"], CRITICAL, "❌"
elif health < 0.875:
    status, s_color, s_icon = t["status_suboptimal"], WARNING, "⚠️"
else:
    status, s_color, s_icon = t["status_optimal"], OPTIMAL, "✅"

# =============================================================================
# 9. ENCABEZADO + PESTAÑAS
# =============================================================================
badge = f'<span class="badge">{t["badge_demo"]}</span>' if is_mock else ""
st.markdown(f'<div class="eyebrow">{t["eyebrow"]}{badge}</div>', unsafe_allow_html=True)
st.title(t["title"])
st.markdown(t["subtitle"])
spacer(0.5)

tab_sim, tab_dash = st.tabs([t["tab_sim"], t["tab_dash"]])

# -----------------------------------------------------------------------------
# TAB 1 · SIMULADOR OPERATIVO
# -----------------------------------------------------------------------------
with tab_sim:
    spacer(0.75)
    col_rx, col_status = st.columns([2.5, 1], gap="large")
    with col_rx:
        rx = (f'<div class="kpi rx"><div class="kpi-label">{t["prescribed"]}</div><div class="rx-values">'
              f'<div><div class="rx-num">pH {res["best_ph"]:.1f}</div><div class="kpi-sub">{t["adjust"]}: {res["best_ph"] - ph:+.1f}</div></div>'
              f'<div><div class="rx-num">EC {res["best_ec"]:.1f} mS</div><div class="kpi-sub">{t["adjust"]}: {res["best_ec"] - ec:+.1f} mS</div></div>'
              f'<div><div class="rx-num" style="color:{OPTIMAL};">{best:.0f} g</div><div class="kpi-sub">{t["target"]}</div></div>'
              f'</div></div>')
        st.markdown(rx, unsafe_allow_html=True)
    with col_status:
        st.markdown(f'<div class="status" style="border-top:6px solid {s_color};"><div class="kpi-label">{t["health_lbl"]}</div>'
                    f'<div class="status-value" style="color:{s_color};">{s_icon} {health * 100:.0f}%</div>'
                    f'<div class="status-text">{status}</div></div>', unsafe_allow_html=True)

    # --- Rendimiento ---
    section(t["sec_yield"], t["sec_yield_cap"])
    k1, k2, k3 = st.columns(3, gap="medium")
    with k1:
        kpi(t["kpi1"], f"{baseline:.1f} g", f"{recoverable_g:.1f} {t['delta']}", s_color)
    with k2:
        kpi(t["kpi2"], f"{best:.1f} g", t["optimized"])
    with k3:
        kpi(t["kpi3"], f"+{uplift_pct:.1f}%", t["impact"], OPTIMAL)

    # --- Impacto financiero ---
    section(t["sec_fin"], t["sec_fin_cap"])
    f1, f2, f3, f4 = st.columns(4, gap="medium")
    with f1:
        kpi(t["fin1"], usd(rev_now), t["fin1_sub"])
    with f2:
        kpi(t["fin2"], usd(rev_opt), t["fin2_sub"])
    with f3:
        kpi(t["fin3"], usd(rev_recover), t["fin3_sub"].format(pct=rev_recover / rev_now * 100 if rev_now > 0 else 0), OPTIMAL)
    with f4:
        kpi(t["fin4"], usd(rev_annual), t["fin4_sub"].format(cycles=int(cycles)), BRAND)
    spacer(0.75)
    with st.container(border=True):
        show(chart_value_bar(rev_now, rev_recover, rev_residual))
        if rev_recover / max(rev_now, 1e-9) < 0.005:
            takeaway(t["fin_take_ok"].format(res=usd(rev_residual)))
        else:
            takeaway(t["fin_take"].format(rec=usd(rev_recover), ann=usd(rev_annual), closed=gap_closed * 100, res=usd(rev_residual)))

    spacer(0.5)
    with st.expander(t["context_title"], expanded=False):
        st.markdown(t["problem"])
        st.markdown(t["solution"])
        st.markdown(t["business"].format(closed=gap_closed * 100))

    # --- Curva pH ---
    section(t["chart_title"], t["chart_cap"])
    with st.container(border=True):
        show(chart_ph_response(res, float(ph)))
        if recoverable_g > 1:
            takeaway(t["ph_take"].format(cur_ph=ph, best_ph=res["best_ph"], cur_ec=ec, best_ec=res["best_ec"], base=baseline, best=best))
        else:
            takeaway(t["ph_take_ok"])

    # --- Auditoría de sensibilidad ---
    section(t["neon_title"], t["neon_cap"])

    def sensitivity_card(title, feature, axis, current, zone, unit, xlabel):
        in_zone = zone[0] <= current <= zone[1]
        color, icon = (OPTIMAL, "✅") if in_zone else (CRITICAL, "❌")
        rng_txt = f"{zone[0]:g}–{zone[1]:g} {unit}"
        msg = (t["in_range"] if in_zone else t["out_range"]).format(rng=rng_txt)
        badge_html = chip(icon + " " + msg, color)
        yields = sensitivity(model, feature, axis, float(temp), float(hum), float(ph), float(ec))
        with st.container(border=True):
            st.markdown(f'<div class="card-head"><span class="card-title">{title}</span>{badge_html}</div>', unsafe_allow_html=True)
            show(chart_sensitivity(axis, yields, float(current), zone, in_zone, xlabel))

    c_temp, c_ec = st.columns(2, gap="large")
    with c_temp:
        sensitivity_card(t["chart_temp"], "temp", TEMP_AXIS, temp, OPT_ZONES["temp"], "°C", t["lbl_temp"])
    with c_ec:
        sensitivity_card(t["chart_ec"], "ec", EC_AXIS, ec, OPT_ZONES["ec"], "mS", t["lbl_ec"])

# -----------------------------------------------------------------------------
# TAB 2 · DASHBOARD EJECUTIVO
# -----------------------------------------------------------------------------
with tab_dash:
    section(t["dash_title"], t["dash_info"])
    val_X, actual, pred, is_demo_val = validation_set(model)

    ss_res, ss_tot = float(np.sum((actual - pred) ** 2)), float(np.sum((actual - actual.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    mae = float(np.mean(np.abs(actual - pred)))

    if is_demo_val:
        takeaway(t["dash_demo_note"], warn=True)
        spacer(0.5)

    d1, d2, d3, d4 = st.columns(4, gap="medium")
    with d1:
        kpi(t["dash_kpi1"], f"{r2 * 100:.1f}%", t["dash_kpi1_sub"] if is_demo_val else t["dash_kpi1_sub_real"], BRAND)
    with d2:
        kpi(t["dash_kpi2"], f"{mae:.1f} g", t["dash_kpi2_sub"])
    with d3:
        kpi(t["dash_kpi3"], f"{glob['ph']:.1f}", t["dash_kpi3_sub"])
    with d4:
        kpi(t["dash_kpi4"], f"{ceiling:.0f} g", t["dash_kpi4_sub"], OPTIMAL)

    spacer(1.25)
    with st.container(border=True):
        st.markdown(f'<div class="card-title">{t["dash_c1_title"]}</div>', unsafe_allow_html=True)
        ph_vals = val_X["pH_Level"].to_numpy(float)
        show(chart_ph_cloud(ph_vals, actual, glob["ph"], float(ph), baseline))
        inside = np.abs(ph_vals - glob["ph"]) <= 0.5
        if inside.any() and (~inside).any():
            med_in, med_out = float(np.median(actual[inside])), float(np.median(actual[~inside]))
            loss = max(0.0, (1 - med_out / med_in) * 100) if med_in > 0 else 0.0
            takeaway(t["dash_c1_take"].format(opt=glob["ph"], loss=loss, med_in=med_in, med_out=med_out))

    spacer(1.0)
    col_l, col_r = st.columns(2, gap="large")
    with col_l:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t["dash_c2_title"]}</div>', unsafe_allow_html=True)
            importances = get_importances(model)
            show(chart_importance(importances))
            share = float(importances[list(CONTROLLABLE_IDX)].sum() / importances.sum())
            takeaway(t["dash_c2_take"].format(share=share))
    with col_r:
        with st.container(border=True):
            st.markdown(f'<div class="card-title">{t["dash_c3_title"]}</div>', unsafe_allow_html=True)
            show(chart_pred_actual(actual, pred, r2, mae))
            takeaway(t["dash_c3_take"].format(mae=mae, r2=r2))

spacer(2.0)
st.caption(t["footer"])
