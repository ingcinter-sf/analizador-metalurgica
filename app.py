import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Analizador Metalúrgica - Perforaciones", layout="wide"
)

st.title("⚙️ Analizador de Planillas de Perforaciones (Metalúrgica)")
st.write(
    "Sube tu archivo CSV para procesar automáticamente las piezas, perfiles y cantidades de agujeros."
)

# Componente para subir el archivo
archivo_subido = st.file_uploader(
    "Sube tu archivo CSV", type=["csv", "txt"]
)

if archivo_subido is not None:
  try:
    # Como el CSV a veces viene con cabeceras desplazadas, leemos línea por línea o usamos pandas adaptado
    # Leemos el archivo ignorando líneas vacías
    lineas = [
        line.decode("utf-8", errors="ignore").strip()
        for line in archivo_subido.readlines()
    ]
    lineas_filtradas = [l for l in lineas if l.replace(",", "").strip() != ""]

    # Buscamos dónde empieza la tabla real (donde dice 'Parte')
    idx_inicio = 0
    for i, linea in enumerate(lineas_filtradas):
      if "Parte" in linea and "Perfil" in linea:
        idx_inicio = i
        break

    # Creamos un DataFrame limpio a partir de la tabla encontrada
    from io import StringIO

    data_str = "\n".join(lineas_filtradas[idx_inicio:])
    df = pd.read_csv(StringIO(data_str))

    # Limpiamos nombres de columnas (eliminando espacios extra)
    df.columns = df.columns.str.strip()

    # Rellenamos los valores hacia abajo (Forward Fill) para las celdas vacías de Parte, Perfil y Cant. Partes
    df["Parte"] = df["Parte"].ffill()
    df["Perfil"] = df["Perfil"].ffill()
    df["Cant. Partes"] = df["Cant. Partes"].ffill()

    # Limpiamos filas donde no haya diámetro o agujeros
    df = df.dropna(subset=["Diametro", "Agujeros por partes"])

    # Asegurar tipos numéricos
    df["Cant. Partes"] = pd.to_numeric(df["Cant. Partes"], errors="coerce")
    df["Diametro"] = pd.to_numeric(df["Diametro"], errors="coerce")
    df["Agujeros por partes"] = pd.to_numeric(
        df["Agujeros por partes"], errors="coerce"
    )

    st.success("¡Archivo analizado con éxito!")

    # Mostrar datos limpios en pantalla
    st.subheader("📋 Datos Limpios Procesados")
    st.dataframe(df)

    # Resumen y cálculos clave
    st.subheader("📊 Resumen de Producción")

    # Calculamos el total de agujeros por pieza y diámetro
    df["Total_Agujeros_Pieza"] = df["Cant. Partes"] * df["Agujeros por partes"]

    # Agrupamos para mostrar un reporte claro
    resumen = (
        df.groupby(["Parte", "Perfil", "Cant. Partes", "Diametro"])
        .agg({"Agujeros por partes": "first", "Total_Agujeros_Pieza": "sum"})
        .reset_index()
    )

    for parte in resumen["Parte"].unique():
      subset = resumen[resumen["Parte"] == parte]
      perfil = subset["Perfil"].iloc[0]
      cant_partes = int(subset["Cant. Partes"].iloc[0])

      st.markdown(f"### Pieza: `{parte}` (Perfil: *{perfil}*)")
      st.info(f"Cantidad de partes a fabricar: **{cant_partes} unidades**")

      for _, row in subset.iterrows():
        st.write(
            f"- **{row['Agujeros por partes']} agujeros** de **{row['Diametro']} mm**"
            f" por pieza. *(Total requerido en las {cant_partes} piezas: **{int(row['Total_Agujeros_Pieza'])} agujeros**)*"
        )

  except Exception as e:
    st.error(
        f"Hubo un error al procesar el archivo. Asegúrate de que el formato"
        f" coincida. Detalle técnico: {e}"
    )
