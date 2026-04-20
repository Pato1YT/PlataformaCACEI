import re
from dataclasses import dataclass, field
from typing import List, Optional

from docx import Document


class ImportadorAtributosWordError(Exception):
    pass


@dataclass
class IndicadorImportado:
    codigo: str
    descripcion: str


@dataclass
class CriterioImportado:
    codigo: str
    descripcion: str
    indicadores: List[IndicadorImportado] = field(default_factory=list)


@dataclass
class AtributoImportado:
    codigo: str
    nombre: str
    criterios: List[CriterioImportado] = field(default_factory=list)


def limpiar_texto(texto: Optional[str]) -> str:
    if not texto:
        return ""
    texto = str(texto).replace("\n", " ")
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def es_marcador_fin(texto: str) -> bool:
    texto_norm = limpiar_texto(texto).lower()

    marcadores = [
        "4. curso",
        "4.a clave",
        "4.b nombre",
        "5. grupo o sección",
        "6. instrumento(s)",
        "7. periodo en el que se evaluó",
        "8. responsable(s)",
        "9. valoración de los resultados",
        "10. meta",
        "instrucciones para el llenado",
    ]

    return any(m in texto_norm for m in marcadores)


def obtener_texto_tablas(doc: Document) -> List[str]:
    """
    Extrae texto útil de las tablas del Word, pero se detiene
    antes de la tabla inferior de cursos/evaluación.
    """
    valores = []

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                texto = limpiar_texto(cell.text)

                if not texto:
                    continue

                if es_marcador_fin(texto):
                    return valores

                valores.append(texto)

    return valores


def extraer_atributo(textos: List[str]) -> AtributoImportado:
    patron_ae = re.compile(r"^(AE\d+)\.\s*(.+)$", re.IGNORECASE)

    for texto in textos:
        match = patron_ae.match(texto)
        if match:
            codigo = match.group(1).upper()
            nombre = limpiar_texto(match.group(2))
            return AtributoImportado(codigo=codigo, nombre=nombre)

    raise ImportadorAtributosWordError(
        "No se pudo identificar el atributo de egreso en el documento."
    )


def es_descripcion_valida(texto: str) -> bool:
    if not texto:
        return False

    texto = limpiar_texto(texto)

    if not texto:
        return False

    texto_lower = texto.lower()

    # No aceptar códigos sueltos
    if re.match(r"^(CD\d+)$", texto, re.IGNORECASE):
        return False

    if re.match(r"^(I\d+)$", texto, re.IGNORECASE):
        return False

    # No aceptar encabezados o basura de la tabla inferior
    valores_invalidos = {
        'cd',
        'in',
        '4. curso',
        '4.a clave',
        '4.b nombre',
        '5. grupo o sección',
        '6. instrumento(s) de evaluación',
        '7. periodo en el que se evaluó',
        '8. responsable(s) de aplicar el instrumento y reportar resultados',
        '9. valoración de los resultados',
        '10. meta',
    }

    if texto_lower in valores_invalidos:
        return False

    if es_marcador_fin(texto):
        return False

    return True


def extraer_criterios_e_indicadores(textos: List[str]) -> List[CriterioImportado]:
    """
    Lee solo la sección AE/CD/I superior del documento.
    Agrupa correctamente criterios e indicadores.
    Ignora indicadores vacíos.
    """
    patron_cd = re.compile(r"^(CD\d+)$", re.IGNORECASE)
    patron_i = re.compile(r"^(I\d+)$", re.IGNORECASE)

    criterios_map = {}
    criterio_actual: Optional[CriterioImportado] = None

    i = 0
    total = len(textos)

    while i < total:
        actual = limpiar_texto(textos[i])

        if es_marcador_fin(actual):
            break

        match_cd = patron_cd.match(actual)
        if match_cd:
            codigo_cd = match_cd.group(1).upper()

            descripcion_cd = ""
            j = i + 1
            while j < total:
                candidato = limpiar_texto(textos[j])

                if es_marcador_fin(candidato):
                    break

                if patron_cd.match(candidato) or patron_i.match(candidato):
                    break

                if es_descripcion_valida(candidato):
                    descripcion_cd = candidato
                    break

                j += 1

            if codigo_cd not in criterios_map:
                criterios_map[codigo_cd] = CriterioImportado(
                    codigo=codigo_cd,
                    descripcion=descripcion_cd,
                    indicadores=[]
                )
            else:
                # Si ya existía pero sin descripción, actualizarla
                if not criterios_map[codigo_cd].descripcion and descripcion_cd:
                    criterios_map[codigo_cd].descripcion = descripcion_cd

            criterio_actual = criterios_map[codigo_cd]
            i += 1
            continue

        match_i = patron_i.match(actual)
        if match_i and criterio_actual:
            codigo_i = match_i.group(1).upper()

            descripcion_i = ""
            j = i + 1
            while j < total:
                candidato = limpiar_texto(textos[j])

                if es_marcador_fin(candidato):
                    break

                if patron_cd.match(candidato) or patron_i.match(candidato):
                    break

                if es_descripcion_valida(candidato):
                    descripcion_i = candidato
                    break

                j += 1

            # Ignorar indicadores vacíos
            if descripcion_i and es_descripcion_valida(descripcion_i):
                ya_existe = any(ind.codigo == codigo_i for ind in criterio_actual.indicadores)
                if not ya_existe:
                    criterio_actual.indicadores.append(
                        IndicadorImportado(
                            codigo=codigo_i,
                            descripcion=descripcion_i,
                        )
                    )

            i += 1
            continue

        i += 1

    # Filtrar criterios totalmente vacíos como CD6, CD7 sin descripción ni indicadores
    criterios_finales = []
    for criterio in criterios_map.values():
        if criterio.descripcion.strip() or criterio.indicadores:
            criterios_finales.append(criterio)

    # Ordenar por número de CD
    criterios_finales.sort(key=lambda c: int(re.search(r"\d+", c.codigo).group()))
    return criterios_finales


def analizar_documento_atributo_word(ruta_archivo: str) -> dict:
    try:
        doc = Document(ruta_archivo)
    except Exception as e:
        raise ImportadorAtributosWordError(
            f"No se pudo leer el documento Word: {str(e)}"
        )

    textos = obtener_texto_tablas(doc)

    if not textos:
        raise ImportadorAtributosWordError(
            "No se encontró contenido útil en las tablas del documento."
        )

    atributo = extraer_atributo(textos)
    criterios = extraer_criterios_e_indicadores(textos)
    atributo.criterios = criterios

    return {
        "atributo": {
            "codigo": atributo.codigo,
            "nombre": atributo.nombre,
        },
        "criterios": [
            {
                "codigo": criterio.codigo,
                "descripcion": criterio.descripcion,
                "indicadores": [
                    {
                        "codigo": indicador.codigo,
                        "descripcion": indicador.descripcion,
                    }
                    for indicador in criterio.indicadores
                ],
            }
            for criterio in atributo.criterios
        ],
    }