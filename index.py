from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px

app = Flask(__name__)

# Cargar los datos globalmente de los años
def cargar_datos():
    try:
        return pd.read_csv('uploads/trabajos_relacionados.csv', encoding='latin')
    except Exception as e:
        print(f"Error al cargar el archivo trabajos_relacionados.csv: {e}")
        return pd.DataFrame()  # Devolver un DataFrame vacío en caso de error

# Cargar el DataFrame al iniciar la app
df_datos = cargar_datos()

@app.route("/")
def index():
    # Preparar datos únicos para los filtros
    años = df_datos['anio'].dropna().unique().tolist()
    temporadas = df_datos['temporada'].dropna().unique().tolist()
    areas_estudio = df_datos['area_de_estudio'].dropna().unique().tolist()
    modelos = df_datos['modelo'].dropna().unique().tolist()
    cultivos = df_datos['cultivo'].dropna().unique().tolist()
    fuentes = df_datos['fuente'].dropna().unique().tolist()
    return render_template(
        "index.html",
        años=años,
        temporadas=temporadas,
        areas_estudio=areas_estudio,
        modelos=modelos,
        cultivos=cultivos,
        fuentes=fuentes
    )

@app.route("/generar_grafico", methods=["GET"])
def generar_grafico():
    try:
        # Obtener los parámetros de los filtros
        año_min = request.args.get("año_min")
        año_max = request.args.get("año_max")
        temporadas = request.args.getlist("temporada")
        areas_estudio = request.args.getlist("area_estudio")
        modelos = request.args.getlist("modelo")
        cultivos = request.args.getlist("cultivo")
        fuente = request.args.get("fuente")

        # Filtrar el DataFrame original
        filtered_df = df_datos.copy()

        # Filtrar por rango de años
        if año_min and año_max:
            filtered_df = filtered_df[(filtered_df["anio"] >= int(año_min)) & (filtered_df["anio"] <= int(año_max))]

        # Filtrar Temporadas
        if temporadas:
            filtered_df = filtered_df[filtered_df["temporada"].isin(temporadas)]

        # Filtrar Áreas de Estudio
        if areas_estudio:
            filtered_df = filtered_df[filtered_df["area_de_estudio"].isin(areas_estudio)]

        # Filtrar Fuente
        if fuente and fuente != "Todos":
            filtered_df = filtered_df[filtered_df["fuente"] == fuente]

        # Filtrar Modelos
        if modelos and "Todos" in modelos:
            filtered_df = filtered_df.assign(modelo=lambda x: x["modelo"] )
        elif modelos:
            filtered_df = filtered_df[filtered_df["modelo"].isin(modelos)]

        # Filtrar Cultivos
        if cultivos and "Todos" in cultivos:
            filtered_df = filtered_df.assign(cultivo=lambda x: x["cultivo"] )
        elif cultivos:
            filtered_df = filtered_df[filtered_df["cultivo"].isin(cultivos)]

        # Formatear las columnas para el hover
        filtered_df["fuente"] = filtered_df["fuente"].str.title()
        filtered_df["area_de_estudio"] = filtered_df["area_de_estudio"].str.title()
        filtered_df["modelo"] = filtered_df["modelo"].str.capitalize()
        filtered_df["cultivo"] = filtered_df["cultivo"].str.title()

        # Crear una columna única para identificar la combinación de fuente, área de estudio y modelo
        filtered_df["fuente_area_modelo"] = filtered_df["fuente"] + " - " + filtered_df["area_de_estudio"] + " - " + filtered_df["modelo"]

        # Crear una función para formatear las etiquetas de la leyenda
        def formatear_etiqueta(texto):
            # Capitalizar la primera letra de cada palabra
            texto = texto.title()
            # Reemplazar guiones por espacios
            texto = texto.replace(" - ", " ")
            return texto

        # Aplicar la función a las etiquetas en la columna 'fuente_area_modelo'
        filtered_df["fuente_area_modelo"] = filtered_df["fuente_area_modelo"].apply(formatear_etiqueta)

        # Validar si hay datos
        if filtered_df.empty:
            return jsonify(success=False, error_message="No hay datos para los filtros seleccionados.")

        # Crear el gráfico
        fig = px.line(
            filtered_df,
            x="anio",
            y="hectareas",
            color="fuente_area_modelo",  # Usar la combinación de fuente, área de estudio y modelo para la leyenda y color
            line_shape="linear",  # Mantener las líneas separadas sin conexión
            markers=True,  # Asegura que se muestren los puntos
            template='ggplot2',
            width=950,
            height=500,
            title="Trabajos relacionados a cultivos",  # Título principal
            labels={
                "anio": "Año",
                "hectareas": "Hectáreas",
                "fuente_area_modelo": "Fuente | Área | Modelo",  # Etiqueta combinada de fuente, área y modelo
            },

        )

        # Crear subtítulo con los filtros separados por "|"
        subtitulo = f"Temporada: {'| '.join(temporadas)}, Área: {'| '.join(areas_estudio)}, Modelo: {'| '.join(modelos)}, Cultivo: {'| '.join(cultivos)}"
        subtitulo = subtitulo.replace(" |", "|").replace("| ", "|")  # Corregir el formato de separación

        # Añadir subtítulo dinámico al gráfico sin alterar la forma del gráfico
        fig.update_layout(
            title_text=f"Trabajos relacionados a cultivos<br><sup>{subtitulo}</sup>",
            title_x=0.5,  # Centrar el título
            title_y=0.95,  # Colocar el título en la parte superior
            title_font=dict(size=18),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12,
                font_family="Arial"
            ),
            plot_bgcolor='rgba(240, 240, 240, 0.9)',  # Fondo gris claro
            paper_bgcolor='rgba(255, 255, 255, 0.9)',  # Fondo blanco para el gráfico
        )

        # Convertir a HTML
        graph_html = fig.to_html(full_html=False)
        return jsonify(success=True, graph_html=graph_html)

    except Exception as e:
        return jsonify(success=False, error_message=str(e))


if __name__ == "__main__":
    app.run(debug=True)
