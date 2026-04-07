import re
import pandas as pd
from unidecode import unidecode
import calendar
from datetime import date

class ImportadorCursosError(Exception):
    pass


def obtener_semestres_validos(periodo):
    nombre = (periodo.nombre or '').upper()

    # Enero - Agosto -> pares
    if 'ENERO' in nombre and 'AGOSTO' in nombre:
        return [2, 4, 6, 8]

    # Agosto - Enero -> impares
    if 'AGOSTO' in nombre and 'ENERO' in nombre:
        return [1, 3, 5, 7]

    # fallback por si el nombre no trae esas palabras completas
    if 'ENE' in nombre and 'AGO' in nombre:
        # si empieza con ENE, asumimos Enero-Agosto
        if nombre.index('ENE') < nombre.index('AGO'):
            return [2, 4, 6, 8]
        return [1, 3, 5, 7]

    # por defecto, impares
    return [1, 3, 5, 7]

MESES_PERIODO = {
    'enero': (1, 'ENE'), 'febrero': (2, 'FEB'), 'marzo': (3, 'MAR'),
    'abril': (4, 'ABR'), 'mayo': (5, 'MAY'), 'junio': (6, 'JUN'),
    'julio': (7, 'JUL'), 'agosto': (8, 'AGO'), 'septiembre': (9, 'SEP'),
    'octubre': (10, 'OCT'), 'noviembre': (11, 'NOV'), 'diciembre': (12, 'DIC'),
}

def parsear_periodo_desde_excel(archivo_excel, nombre_hoja):
    """
    Lee la columna 'Periodo' del Excel y extrae las fechas para generar
    automáticamente el código y nombre del periodo.
    Ejemplo: 'Enero 2026 - Junio 2026' -> codigo='ENE26JUN26'
    Retorna un dict con codigo, nombre, fecha_inicio, fecha_fin o None si no se pudo.
    """
    try:
        df = pd.read_excel(archivo_excel, sheet_name=nombre_hoja)
    except Exception:
        return None

    if 'Periodo' not in df.columns:
        return None

    # Buscar el primer valor de Periodo que parezca un rango de fechas
    for valor in df['Periodo'].dropna():
        texto = str(valor).strip().lower()
        patron = r'(\w+)\s+(\d{4})\s*[-–]\s*(\w+)\s+(\d{4})'
        m = re.search(patron, texto)
        if not m:
            continue

        mes_inicio_str, anio_inicio, mes_fin_str, anio_fin = m.groups()

        if mes_inicio_str not in MESES_PERIODO or mes_fin_str not in MESES_PERIODO:
            continue

        num_inicio, abr_inicio = MESES_PERIODO[mes_inicio_str]
        num_fin, abr_fin = MESES_PERIODO[mes_fin_str]

        year_inicio = int(anio_inicio)
        year_fin = int(anio_fin)

        codigo = f'{abr_inicio}{str(year_inicio)[2:]}{abr_fin}{str(year_fin)[2:]}'
        nombre = f'{abr_inicio} {year_inicio} - {abr_fin} {year_fin}'

        fecha_inicio = date(year_inicio, num_inicio, 1)
        ultimo_dia = calendar.monthrange(year_fin, num_fin)[1]
        fecha_fin = date(year_fin, num_fin, ultimo_dia)

        return {
            'codigo': codigo,
            'nombre': nombre,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
        }

    return None

def convertir_semestre_a_numero(valor):
    if pd.isna(valor):
        return None

    texto = str(valor).strip().lower()
    texto = texto.replace('\n', ' ')
    texto = re.sub(r'\s+', ' ', texto)

    match = re.search(r'(\d+)', texto)
    if match:
        return int(match.group(1))

    return None


def normalizar_clave(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()

    # distintos guiones raros -> guion normal
    texto = (
        texto.replace('–', '-')
             .replace('—', '-')
             .replace('−', '-')
             .replace('‐', '-')
             .replace('-', '-')
             .replace('﹣', '-')
             .replace('－', '-')
    )

    # caracteres basura frecuentes
    texto = texto.replace('￾', '-')
    texto = texto.replace('�', '-')

    # quitar espacios alrededor del guion
    texto = re.sub(r'\s*-\s*', '-', texto)

    # si no trae guion pero parece clave tipo ACC0906 -> ACC-0906
    texto = re.sub(r'^([A-Z]+)\s*([0-9]{4})$', r'\1-\2', texto)

    # limpiar caracteres extraños dejando letras, numeros y guion
    texto = re.sub(r'[^A-Z0-9-]', '', texto)

    return texto


def normalizar_nombre_docente(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if not texto or texto.lower() == 'nan':
        return ""

    texto = texto.replace('\n', ' ')
    texto = re.sub(r'\s+', ' ', texto).strip()

    # quitar títulos comunes al inicio
    patrones = [
        r'^\s*ing\.?\s+',
        r'^\s*lic\.?\s+',
        r'^\s*mii\.?\s+',
        r'^\s*mtro\.?\s+',
        r'^\s*mtra\.?\s+',
        r'^\s*dr\.?\s+',
        r'^\s*dra\.?\s+',
        r'^\s*mc\.?\s+',
        r'^\s*arq\.?\s+',
    ]

    for patron in patrones:
        texto = re.sub(patron, '', texto, flags=re.IGNORECASE)

    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def normalizar_nombre_para_match(valor):
    texto = normalizar_nombre_docente(valor)
    texto = unidecode(texto.lower())
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def obtener_hojas_excel_cursos(archivo_excel):
    try:
        excel_file = pd.ExcelFile(archivo_excel)
        return excel_file.sheet_names
    except Exception as e:
        raise ImportadorCursosError(f"No se pudo leer el archivo Excel: {str(e)}")


def normalizar_columnas(df):
    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df


def preparar_dataframe_cursos(df):
    df = normalizar_columnas(df)

    # quitar columnas totalmente vacías
    df = df.dropna(axis=1, how='all')

    rename_map = {}

    for col in df.columns:
        col_lower = str(col).strip().lower()

        if col_lower == 'clave':
            rename_map[col] = 'clave'
        elif col_lower in ['asignatura', 'materia', 'nombre']:
            rename_map[col] = 'materia'
        elif col_lower == 'semestre':
            rename_map[col] = 'semestre'
        elif col_lower == 'docente':
            rename_map[col] = 'docente'

    df = df.rename(columns=rename_map)

    columnas_requeridas = ['clave', 'materia', 'semestre', 'docente']
    for columna in columnas_requeridas:
        if columna not in df.columns:
            raise ImportadorCursosError(f"No se encontró la columna requerida: {columna}")

    # rellenar agrupaciones visuales del excel
    df['semestre'] = df['semestre'].ffill()
    df['docente'] = df['docente'].ffill()

    # limpiar texto base
    df['clave'] = df['clave'].apply(normalizar_clave)
    df['materia'] = df['materia'].astype(str).str.strip()
    df['docente'] = df['docente'].apply(normalizar_nombre_docente)

    # convertir semestre
    df['semestre_num'] = df['semestre'].apply(convertir_semestre_a_numero)

    # filtrar filas basura
    df = df[
        (df['clave'] != '') &
        (df['clave'].str.lower() != 'nan')
    ].copy()

    return df


def analizar_hoja_cursos(archivo_excel, nombre_hoja, periodo, materias_queryset, docentes_queryset, cursos_queryset):
    try:
        df = pd.read_excel(archivo_excel, sheet_name=nombre_hoja)
    except Exception as e:
        raise ImportadorCursosError(f"No se pudo leer la hoja '{nombre_hoja}': {str(e)}")

    df = preparar_dataframe_cursos(df)

    semestres_validos = obtener_semestres_validos(periodo)

    # catálogos normalizados
    materias_por_clave = {}
    for materia in materias_queryset:
        materias_por_clave[normalizar_clave(materia.clave)] = materia

    docentes_normalizados = []
    for docente in docentes_queryset:
        nombre_completo = docente.get_full_name() or docente.username
        docentes_normalizados.append({
            'obj': docente,
            'nombre_normalizado': normalizar_nombre_para_match(nombre_completo),
        })

    preview_data = []

    for _, row in df.iterrows():
        clave = row.get('clave', '')
        nombre_materia = str(row.get('materia', '')).strip()
        docente_excel = row.get('docente', '')
        semestre = row.get('semestre_num', None)

        estado = ''
        docente_encontrado = None
        materia_encontrada = materias_por_clave.get(clave)

        # buscar docente por nombre normalizado
        docente_normalizado = normalizar_nombre_para_match(docente_excel)
        if docente_normalizado:
            for item in docentes_normalizados:
                nombre_docente = item['nombre_normalizado']

                if docente_normalizado == nombre_docente:
                    docente_encontrado = item['obj']
                    break

                if docente_normalizado in nombre_docente or nombre_docente in docente_normalizado:
                    docente_encontrado = item['obj']
                    break

        if semestre is None:
            estado = 'Semestre inválido'
        elif semestre not in semestres_validos:
            estado = 'No corresponde al periodo'
        elif not materia_encontrada:
            estado = 'Materia no encontrada'
        elif not docente_encontrado:
            estado = 'Docente no encontrado'
        else:
            existe = cursos_queryset.filter(
                materia=materia_encontrada,
                periodo=periodo,
                docente=docente_encontrado,
                grupo='A'
            ).exists()

            if existe:
                estado = 'Curso ya existe'
            else:
                estado = 'Listo para crear'

        semestre_preview = int(semestre) if pd.notna(semestre) else ''

        preview_data.append({
            'clave': clave,
            'materia': nombre_materia,
            'semestre': semestre_preview,
            'docente': docente_excel,
            'docente_id': docente_encontrado.id if docente_encontrado else None,
            'materia_id': materia_encontrada.id if materia_encontrada else None,
            'estado': estado,
        })

    return preview_data