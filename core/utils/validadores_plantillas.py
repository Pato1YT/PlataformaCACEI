from docxtpl import DocxTemplate


PLACEHOLDERS_REPORTE_NIVEL_LOGRO = {
    'clave_curso',
    'semestre',
    'nombre_curso',
    'codigo_atributo',
    'descripcion_atributo',
    'descripcion_criterio',
    'descripcion_indicador',
    'instrumento_evaluacion',
    'alumnos_evaluados',
    'porcentaje_meta',
    'porcentaje_obtenido',
    'argumentacion',
    'acciones_mejora',
}


def obtener_placeholders_docx(ruta_archivo):
    doc = DocxTemplate(ruta_archivo)
    return doc.get_undeclared_template_variables()


def validar_placeholders_reporte_nivel_logro(ruta_archivo):
    encontrados = obtener_placeholders_docx(ruta_archivo)
    faltantes = PLACEHOLDERS_REPORTE_NIVEL_LOGRO - encontrados

    return {
        'es_valida': not faltantes,
        'encontrados': sorted(encontrados),
        'faltantes': sorted(faltantes),
    }