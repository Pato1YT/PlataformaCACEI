import os
from decimal import Decimal

from django.conf import settings
from django.core.files import File
from docxtpl import DocxTemplate

from core.models import EvidenciaIndicador


class GeneradorReporteNivelLogroError(Exception):
    pass


def formatear_porcentaje(valor):
    if valor is None:
        return ""

    if isinstance(valor, Decimal):
        valor = float(valor)

    if float(valor).is_integer():
        return f"{int(valor)}%"

    return f"{valor}%"


def obtener_semestre_texto(numero):
    mapa = {
        1: "Primero",
        2: "Segundo",
        3: "Tercero",
        4: "Cuarto",
        5: "Quinto",
        6: "Sexto",
        7: "Séptimo",
        8: "Octavo",
        9: "Noveno",
    }

    return mapa.get(numero, str(numero))


def generar_reporte_nivel_logro(resultado):
    curso = resultado.curso
    materia = curso.materia
    periodo = materia.periodo
    indicador = resultado.indicador
    criterio = indicador.criterio
    atributo = criterio.atributo_egreso

    plantilla = getattr(periodo, 'plantilla_reporte_nivel_logro', None)

    if not plantilla:
        raise GeneradorReporteNivelLogroError(
            f'No hay plantilla de reporte configurada para el periodo {periodo.codigo}.'
        )

    if not plantilla.archivo:
        raise GeneradorReporteNivelLogroError(
            f'La plantilla del periodo {periodo.codigo} no tiene archivo.'
        )

    ruta_plantilla = plantilla.archivo.path

    if not os.path.exists(ruta_plantilla):
        raise GeneradorReporteNivelLogroError(
            'No se encontró el archivo físico de la plantilla.'
        )

    doc = DocxTemplate(ruta_plantilla)

    contexto = {
        'clave_curso': materia.clave,
        'semestre': obtener_semestre_texto(materia.semestre),
        'nombre_curso': materia.nombre,
        'codigo_atributo': atributo.codigo,
        'descripcion_atributo': atributo.descripcion,
        'descripcion_criterio': criterio.descripcion,
        'descripcion_indicador': indicador.descripcion,
        'instrumento_evaluacion': resultado.instrumento_evaluacion,
        'alumnos_evaluados': resultado.alumnos_evaluados,
        'porcentaje_meta': formatear_porcentaje(resultado.porcentaje_meta),
        'porcentaje_obtenido': formatear_porcentaje(resultado.porcentaje_obtenido),
        'argumentacion': resultado.argumentacion,
        'acciones_mejora': resultado.acciones_mejora,
    }

    doc.render(contexto)

    nombre_archivo = (
        f"reporte_nivel_logro_"
        f"{materia.clave}_"
        f"{atributo.codigo}_"
        f"{criterio.codigo}_"
        f"{indicador.codigo}_"
        f"curso_{curso.id}.docx"
    ).replace(" ", "_")

    carpeta_salida = os.path.join(
        settings.MEDIA_ROOT,
        'reportes_generados',
        f'curso_{curso.id}',
    )
    os.makedirs(carpeta_salida, exist_ok=True)

    ruta_salida = os.path.join(carpeta_salida, nombre_archivo)
    doc.save(ruta_salida)

    evidencia, _ = EvidenciaIndicador.objects.update_or_create(
        curso=curso,
        indicador=indicador,
        tipo_archivo='REPORTE',
        defaults={
            'titulo': 'Reporte de nivel de logro',
        }
    )

    with open(ruta_salida, 'rb') as archivo:
        evidencia.archivo.save(nombre_archivo, File(archivo), save=True)

    return evidencia