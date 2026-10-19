import os
import streamlit as st
import numpy as np
import pandas as pd
import calculos as sismico

st.set_page_config(
    page_title="Análisis Modal Espectral E.030",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Plataforma Web: Análisis Dinámico Modal Espectral")
st.markdown("**Especialización Python + IA (AECODE / CIP)** | Automatización de cálculo sísmico matricial, visualización e informes técnicos.")

# =====================================================================
# BARRA LATERAL: PARÁMETROS EDITABLES (MÁS DE 5 INPUTS MANUALES)
# =====================================================================
st.sidebar.header("⚙️ 1. Parámetros Sísmicos (Carga Manual)")
st.sidebar.caption("Modifica los coeficientes normativos en tiempo real:")

Z = st.sidebar.number_input("Factor de Zona (Z)", min_value=0.10, max_value=0.60, value=0.45, step=0.05)
U = st.sidebar.number_input("Factor de Uso (U)", min_value=1.00, max_value=2.00, value=1.00, step=0.05)
S = st.sidebar.number_input("Factor de Suelo (S)", min_value=0.80, max_value=2.00, value=1.00, step=0.05)
R = st.sidebar.number_input("Coeficiente de Reducción (R)", min_value=1.0, max_value=12.0, value=8.0, step=0.5)
Tp = st.sidebar.number_input("Periodo de Plataforma Tp (s)", min_value=0.10, max_value=1.50, value=0.40, step=0.05)
TL = st.sidebar.number_input("Periodo Límite TL (s)", min_value=1.00, max_value=4.00, value=2.50, step=0.10)
g = st.sidebar.number_input("Aceleración de la Gravedad g (m/s²)", min_value=9.70, max_value=9.90, value=9.81, step=0.01)

st.sidebar.markdown("---")
st.sidebar.subheader("⏱️ Periodos Modales (s)")
col_t1, col_t2, col_t3 = st.sidebar.columns(3)
T1 = col_t1.number_input("T1 (s)", value=0.556, format="%.3f", step=0.01)
T2 = col_t2.number_input("T2 (s)", value=0.193, format="%.3f", step=0.01)
T3 = col_t3.number_input("T3 (s)", value=0.126, format="%.3f", step=0.01)
T_modos = np.array([T1, T2, T3])

params = {'Z': Z, 'U': U, 'S': S, 'R': R, 'Tp': Tp, 'TL': TL, 'g': g}

# =====================================================================
# SECCIÓN DE CARGA DE DATOS (ARCHIVO EXCEL/CSV O EDICIÓN MANUAL)
# =====================================================================
df_default = pd.DataFrame({
    'Piso': [5, 4, 3, 2, 1],
    'Masa': [27.50, 31.80, 31.80, 31.80, 31.80],
    'Phi_1': [0.10834, 0.09940, 0.08302, 0.05959, 0.03112],
    'Phi_2': [0.10609, 0.03358, -0.05484, -0.10193, -0.08102],
    'Phi_3': [0.09176, -0.05769, -0.09525, 0.03021, 0.10415]
})

with st.expander("📂 2. Carga de Datos Estructurales (Desde Archivo o Edición Manual en Tabla)", expanded=True):
    col_up, col_dl = st.columns([2, 1])
    with col_up:
        archivo_subido = st.file_uploader(
            "Sube un archivo CSV o Excel (.xlsx) con las columnas: Piso, Masa, Phi_1, Phi_2, Phi_3",
            type=["csv", "xlsx"]
        )
    with col_dl:
        st.write("¿Necesitas un archivo de prueba?")
        csv_plantilla = df_default.to_csv(index=False).encode('utf-8')
        st.download_button(
            "⬇️ Descargar Plantilla CSV",
            data=csv_plantilla,
            file_name="plantilla_datos_sismicos.csv",
            mime="text/csv"
        )

    if archivo_subido is not None:
        if archivo_subido.name.endswith('.csv'):
            df_input = pd.read_csv(archivo_subido)
        else:
            df_input = pd.read_excel(archivo_subido)
        st.success("✅ Archivo cargado correctamente.")
    else:
        st.info("💡 Usando datos por defecto del edificio de 5 niveles (puedes editarlos haciendo doble clic en cualquier celda):")
        df_input = df_default.copy()

    df_editado = st.data_editor(df_input, num_rows="dynamic", use_container_width=True)

pisos = df_editado['Piso'].to_numpy(dtype=int)
masa = df_editado['Masa'].to_numpy(dtype=float)
phi = df_editado[['Phi_1', 'Phi_2', 'Phi_3']].to_numpy(dtype=float)

# =====================================================================
# EJECUCIÓN DEL MOTOR DE CÁLCULO (DESDE LA LIBRERÍA calculos.py)
# =====================================================================
res = sismico.ejecutar_analisis_completo(pisos, masa, phi, T_modos, params)
df_modos = res['df_modos']
df_resultados = res['df_resultados']

# =====================================================================
# INTERPRETACIÓN INGENIERIL Y MÉTRICAS CLAVE
# =====================================================================
st.subheader("📊 3. Resumen Ejecutivo e Interpretación Estructural")
v_basal_modos = np.abs(res['V_modos'][-1, :])
modo_dominante = np.argmax(v_basal_modos) + 1
pct_dominante = (v_basal_modos[modo_dominante - 1] / np.sum(v_basal_modos)) * 100
vreal_base = df_resultados['Vreal (tonf)'].iloc[-1]
vrnch_base = df_resultados['Vrnc_h (tonf)'].iloc[-1]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Modo Dominante en Base", f"Modo {modo_dominante}", f"{pct_dominante:.1f}% del V_sum_abs")
m2.metric("Cortante Basal Modo 1 (V_M1)", f"{v_basal_modos[0]:.2f} tonf", f"Γ₁ = {res['Gamma'][0]:.2f}")
m3.metric("Cortante Combinado (Vrnc_h)", f"{vrnch_base:.2f} tonf", "0.25·Vabs + 0.75·Vrcsc")
m4.metric("Cortante Real 1er Piso (Vreal)", f"{vreal_base:.2f} tonf", f"Factor 0.75·R = {0.75*R:.1f}")

st.success(
    f"**Interpretación Técnica:** El **Modo {modo_dominante}** gobierna la respuesta dinámica en la base con un cortante modal de "
    f"**{v_basal_modos[0]:.2f} tonf** (frente a {v_basal_modos[1]:.2f} tonf del Modo 2 y {v_basal_modos[2]:.2f} tonf del Modo 3), "
    f"debido a su alto factor de participación modal ($\Gamma_1 = {res['Gamma'][0]:.2f}$). Tras aplicar la combinación normativa "
    f"y el factor de escalamiento ($0.75 \cdot R$), el **Cortante Real de Diseño ($V_{{real}}$) en el primer piso alcanza {vreal_base:.2f} tonf**."
)

# =====================================================================
# TABLAS DESPLEGABLES Y BOTÓN DE EXPORTACIÓN
# =====================================================================
tab_t1, tab_t2 = st.tabs(["📋 Tabla de Resultados por Nivel", "🔬 Propiedades Dinámicas por Modo"])
with tab_t1:
    st.dataframe(df_resultados.style.format(precision=2), use_container_width=True)
with tab_t2:
    st.dataframe(df_modos.style.format(precision=3), use_container_width=True)

excel_bytes = sismico.generar_excel_en_memoria(params, df_modos, df_resultados)
st.download_button(
    label="📥 Exportar Informe Técnico Completo en Excel (.xlsx)",
    data=excel_bytes,
    file_name="Reporte_Tecnico_Sismico_E030.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary"
)

st.markdown("---")

# =====================================================================
# GENERACIÓN Y VISUALIZACIÓN DINÁMICA DE GIFS EN MOVIMIENTO
# =====================================================================
st.markdown("---")
st.subheader("🎥 5. Animaciones Dinámicas Automáticas (GIFs Modales)")
st.markdown("Generando y actualizando las animaciones modales armónicas en función de tus datos actuales:")

import matplotlib.animation as animation
from matplotlib.animation import PillowWriter

os.makedirs("resultados_graficos", exist_ok=True)
pisos_con_base = np.append(pisos, 0)
t_frames = np.linspace(0, 2*np.pi, 25)

# Generar los 3 GIFs automáticamente en tiempo de ejecución con los nuevos Phi y T
col_g1, col_g2, col_g3 = st.columns(3)
columnas_gif = [col_g1, col_g2, col_g3]

for i in range(3):
    fig_g, ax_g = plt.subplots(figsize=(4, 6))
    ax_g.set_xlim(-0.2, 0.2)
    ax_g.set_ylim(0, max(pisos) + 1)
    ax_g.set_title(f'Modo {i+1} ($T_{{ {i+1} }} = {T_modos[i]:.3f}$s)')
    ax_g.set_ylabel('Piso')
    ax_g.set_xlabel('Amplitud Relativa')
    ax_g.set_yticks(pisos_con_base)
    ax_g.grid(True, linestyle='--', alpha=0.5)
    ax_g.axvline(x=0, color='black', linewidth=1, alpha=0.5)
    
    line_g, = ax_g.plot([], [], 'o-', lw=3, color='#800000', markersize=8)
    
    def animate_func(frame, mode_idx=i):
        disp = np.append(phi[:, mode_idx] * np.sin(frame), 0)
        line_g.set_data(disp, pisos_con_base)
        return line_g,

    ani = animation.FuncAnimation(fig_g, animate_func, frames=t_frames, interval=100, blit=True)
    ruta_gif_dinamico = f"resultados_graficos/03_Animacion_Modo_{i+1}.gif"
    ani.save(ruta_gif_dinamico, writer=PillowWriter(fps=15))
    plt.close(fig_g)
    
    # Mostrar el GIF animado en su respectiva columna en Streamlit
    with columnas_gif[i]:
        st.markdown(f"**Modo {i+1}** ($T_{{ {i+1} }} = {T_modos[i]:.3f}$s)")
        st.image(ruta_gif_dinamico, use_container_width=True)

