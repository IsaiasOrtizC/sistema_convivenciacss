"""Utilidades para armar reportes descargables (PDF y XLSX)."""

from django.db import connection
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors

from ..trazabilidad import trazar


@trazar('SERVICE', 'ReporteService', 'preparando los datos del reporte del caso')
def datos_reporte_caso(caso):
    texto = caso.caso_descripcion or ''
    titulo = f'Caso #{caso.caso_id}'
    descripcion = texto
    if texto.startswith('[') and '] - ' in texto:
        titulo, descripcion = texto[1:].split('] - ', 1)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT e.estudiante_identificador, e.estudiante_nombre,
                   e.estudiante_apaterno, e.estudiante_amaterno,
                   cu.curso_grado, cu.curso_letra, i.tipo_falta
            FROM involucran i
            JOIN estudiante e ON e.estudiante_id = i.estudiante_id
            JOIN curso cu ON cu.curso_id = e.curso_id
            WHERE i.caso_id = %s
            ORDER BY e.estudiante_apaterno, e.estudiante_nombre
            """,
            [caso.caso_id],
        )
        involucrados = cursor.fetchall()

    return {
        'id': caso.caso_id,
        'titulo': titulo.strip(),
        'descripcion': descripcion.strip(),
        'fecha': caso.caso_fecha,
        'lugar': caso.lugar.lugar_nombre if caso.lugar else 'No especificado',
        'involucrados': [
            {
                'identificador': identificador or '',
                'nombre': f'{nombre} {apaterno} {amaterno}'.strip(),
                'curso': f'{grado} {letra}',
                'tipo_falta': tipo_falta,
            }
            for identificador, nombre, apaterno, amaterno, grado, letra, tipo_falta
            in involucrados
        ],
    }


def valor_xlsx_seguro(valor):
    if isinstance(valor, str) and valor.startswith(('=', '+', '-', '@')):
        return f"'{valor}"
    return valor


@trazar('SERVICE', 'ReporteService', 'dibujando gráfico de barras', nivel_min=2)
def crear_grafico_barras_pdf(labels, data, ancho=460, alto=190):
    drawing = Drawing(ancho, alto)
    chart = VerticalBarChart()
    chart.x = 45
    chart.y = 40
    chart.width = ancho - 70
    chart.height = alto - 60
    chart.data = [data if data else [0]]
    chart.categoryAxis.categoryNames = labels if labels else ['Sin datos']
    chart.categoryAxis.labels.angle = 25
    chart.categoryAxis.labels.dy = -12
    chart.categoryAxis.labels.fontSize = 7
    chart.valueAxis.valueMin = 0
    chart.bars[0].fillColor = colors.HexColor('#7B1A1A')
    drawing.add(chart)
    return drawing


@trazar('SERVICE', 'ReporteService', 'dibujando gráfico de torta', nivel_min=2)
def crear_grafico_torta_pdf(labels, data, ancho=460, alto=210):
    drawing = Drawing(ancho, alto)
    pie = Pie()
    pie.x = 150
    pie.y = 25
    pie.width = 150
    pie.height = 150
    tiene_datos = sum(data) > 0 if data else False
    pie.data = data if tiene_datos else [1]
    pie.labels = labels if tiene_datos else ['Sin datos']
    paleta = [colors.HexColor('#7B1A1A'), colors.HexColor('#D4A017'), colors.HexColor('#1E8449'),
              colors.HexColor('#2874A6'), colors.HexColor('#B7860B'), colors.HexColor('#8E44AD'),
              colors.HexColor('#C0392B'), colors.HexColor('#16A085')]
    for i in range(len(pie.data)):
        pie.slices[i].fillColor = paleta[i % len(paleta)]
    drawing.add(pie)
    return drawing
