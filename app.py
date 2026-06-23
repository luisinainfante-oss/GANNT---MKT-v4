import streamlit as st
import pandas as pd
from datetime import datetime
import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io

# Configuración de página de la App Web
st.set_page_config(page_title="Fábrica de Gantt - Marketing", layout="wide")

# ==========================================
# DEFINE LAS IDENTIDADES DE MARCA
# ==========================================
ESTILOS_MARCAS = {
    "FULL_SPORT": {
        "bg_primary": "#000000", "accent_primary": "#FF00FF", "accent_secondary": "#00E5FF",
        "text_main": "#FFFFFF", "text_dim": "#8E8E93", "border_color": "#2C2C2E"
    },
    "VILLAVICENCIO": {
        "bg_primary": "#FFFFFF", "accent_primary": "#00A3E0", "accent_secondary": "#E4002B",
        "text_main": "#1C1C1E", "text_dim": "#636366", "border_color": "#E5E5EA"
    },
    "VDS": {
        "bg_primary": "#0A192F", "accent_primary": "#00B4D8", "accent_secondary": "#FF8A7A",
        "text_main": "#F8F9FA", "text_dim": "#94A3B8", "border_color": "#1E293B"
    },
    "LEVITE": {
        "bg_primary": "#F4F9F4", "accent_primary": "#005A9C", "accent_secondary": "#A3E4D7",
        "text_main": "#1E3A1E", "text_dim": "#7A9A7A", "border_color": "#E0EBE0"
    }
}

st.title("🛠️ La Fábrica de Gantt de Marketing")
st.markdown("Pegá tu tabla de Excel, elegí tu marca y bajá tu slide en PNG de forma automática.")

# ==========================================
# PANEL LATERAL - CONFIGURACIÓN DE MARCA
# ==========================================
with st.sidebar:
    st.header("🎨 Personalización")
    marca = st.selectbox("Elegí la Marca:", list(ESTILOS_MARCAS.keys()))
    config = ESTILOS_MARCAS[marca]
    
    proyecto_tag = st.text_input("Subtítulo de la slide:", "CRONOGRAMA DE OPERACIONES 2026")
    titulo_slide = st.text_input("Título principal:", "Lanzamiento Estratégico de Campaña")

# ==========================================
# PANEL PRINCIPAL - CARGA DE DATOS
# ==========================================
st.subheader("📋 Paso 1: Pegá tus celdas de Excel abajo")
data_input = st.text_area("Pegá acá tus datos de Excel directamente:", height=180)

if data_input:
    try:
        lines = [line.strip() for line in data_input.strip().split('\n') if line.strip()]
        
        tareas_lista = []
        hitos_lista = []
        fecha_pattern = r'\b\d{1,2}/\d{1,2}/\d{4}\b'
        
        for line in lines:
            fechas_encontradas = re.findall(fecha_pattern, line)
            if not fechas_encontradas:
                continue
            
            partes = re.split(r'\t|\s{2,}', line)
            name = partes[0] if partes else "Tarea Sin Nombre"
            
            # Clasificación inteligente de Hito vs Barra de proceso
            if any(k in name.lower() for k in ["launch", "aprobacion", "aprobación", "apertura", "confirmation", "hito"]):
                fec = datetime.strptime(fechas_encontradas[0], "%d/%m/%Y")
                hitos_lista.append({"name": name, "date": fec})
            else:
                if len(fechas_encontradas) >= 2:
                    ini = datetime.strptime(fechas_encontradas[0], "%d/%m/%Y")
                    fin = datetime.strptime(fechas_encontradas[1], "%d/%m/%Y")
                    tareas_lista.append({"name": name, "start": ini, "end": fin})

        # Ordenar en cascada (la fecha más temprana va arriba de todo)
        tareas_lista = sorted(tareas_lista, key=lambda x: x["start"], reverse=True)

        if not tareas_lista and not hitos_lista:
            st.warning("No se encontraron datos válidos. Comprobá las fechas.")
            st.stop()

        # ==========================================
        # MOTOR DE GRÁFICO PREMIUM CORPORATIVO (16:9)
        # ==========================================
        fig, ax = plt.subplots(figsize=(13.333, 7.5), dpi=150)
        fig.patch.set_facecolor(config["bg_primary"])
        ax.set_facecolor(config["bg_primary"])

        # Encontrar rango de fechas global para el encuadre
        todas_fechas = []
        for t in tareas_lista: todas_fechas.extend([t["start"], t["end"]])
        for h in hitos_lista: todas_fechas.append(h["date"])
        
        min_p, max_p = min(todas_fechas), max(todas_fechas)
        margin_start = min_p - pd.Timedelta(days=15)
        margin_end = max_p + pd.Timedelta(days=15)

        # Dibujar Barras de Proceso Estilo "Bloque de Color"
        for i, t in enumerate(tareas_lista):
            color_bar = config["accent_primary"] if i % 2 == 0 else config["accent_secondary"]
            duracion = (t["end"] - t["start"]).days
            if duracion <= 0: duracion = 1
            
            # Dibujar la barra compacta
            ax.barh(i + 1, duracion, left=t["start"], height=0.5, 
                    color=color_bar, edgecolor='none', alpha=0.95, zorder=3)
            
            # Texto a la izquierda de la barra bien alineado
            ax.text(t["start"] - pd.Timedelta(days=5), i + 1, t["name"].upper(), color=config["text_main"], 
                    fontsize=8.5, fontweight='bold', va='center', ha='right')
            
            # Fechas sutiles a la derecha del bloque
            fechas_str = f"{t['start'].strftime('%d/%m')} - {t['end'].strftime('%d/%m')}"
            ax.text(t["end"] + pd.Timedelta(days=5), i + 1, fechas_str, color=config["text_dim"], 
                    fontsize=7.5, va='center', ha='left')

        # Eje Base para los Hitos de Aprobación
        ax.axhline(y=0, color=config["text_main"], linewidth=1.5, zorder=2)
        
        # Dibujar pins de Hitos inferiores
        for h in hitos_lista:
            ax.plot([h["date"], h["date"]], [-0.15, 0.15], color=config["accent_secondary"], linewidth=1.8, zorder=4)
            
            texto_hito = f"{h['date'].strftime('%d/%m')}\n{h['name'].upper()}"
            ax.text(h["date"], -0.4, texto_hito, color=config["text_main"],
                    fontsize=7.5, fontweight='bold', va='top', ha='center',
                    bbox=dict(facecolor=config["bg_primary"], edgecolor='none', pad=1))

        # Ajustes de la línea de tiempo superior (Meses)
        ax.set_yticks([])
        ax.set_ylim(-1.8, len(tareas_lista) + 1.5)
        ax.set_xlim(margin_start, margin_end)
        
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b \'%y'))
        
        ax.tick_params(axis='x', colors=config["text_dim"], labelsize=9.5, pad=8)
        ax.xaxis.tick_top()
        
        # Ocultar marcos por defecto
        for spine in ["left", "right", "bottom", "top"]:
            ax.spines[spine].set_visible(False)
            
        ax.spines["top"].set_color(config["border_color"])
        ax.spines["top"].set_visible(True)
        ax.spines["top"].set_linewidth(1.5)

        # Encabezados limpios integrados
        plt.text(0.04, 0.94, proyecto_tag.upper(), transform=fig.transFigure, color=config["accent_primary"], fontsize=11, fontweight='bold')
        plt.text(0.04, 0.88, titulo_slide.upper(), transform=fig.transFigure, color=config["text_main"], fontsize=22, fontweight='bold')
        
        # Footer institucional
        plt.text(0.04, 0.04, f"{marca.replace('_', ' ')} / CREATIVE & OPERATIONS", transform=fig.transFigure, color=config["text_main"], fontsize=9, fontweight='bold')
        plt.text(0.96, 0.04, "DIAPOSITIVA AUTOMATIZADA", transform=fig.transFigure, color=config["text_dim"], fontsize=9, ha='right')

        plt.tight_layout()
        plt.subplots_adjust(top=0.75, bottom=0.20, left=0.25, right=0.90)

        # Exportación a memoria limpia
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
        img_buffer.seek(0)
        plt.close()

        # Renderizar resultado en pantalla
        st.subheader("🖼️ Paso 2: Tu Diapositiva está lista")
        st.image(img_buffer, use_column_width=True)

        # Botón nativo de guardado directo
        st.download_button(
            label="📥 Descargar Diapositiva en PNG",
            data=img_buffer,
            file_name=f"Gantt_{marca}_{datetime.now().strftime('%Y%m%d')}.png",
            mime="image/png"
        )

    except Exception as e:
        st.error(f"Error al procesar el Excel. Asegurate de que los datos tengan fechas válidas. Detalles: {e}")