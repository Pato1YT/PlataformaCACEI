import re
import pandas as pd


class ImportadorMateriasError(Exception):
    pass


def obtener_hojas_excel(archivo_excel):
    try:
        excel_file = pd.ExcelFile(archivo_excel)
        return excel_file.sheet_names
    except Exception as e:
        raise ImportadorMateriasError(f"No se pudo leer el archivo Excel: {str(e)}")


def normalizar_columnas(df):
    df = df.copy()
    df.columns = [str(col).strip().lower() for col in df.columns]
    return df


def normalizar_clave(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()

    texto = (
        texto.replace('–', '-')
             .replace('—', '-')
             .replace('−', '-')
             .replace('‐', '-')
             .replace('﹣', '-')
             .replace('－', '-')
             .replace('￾', '-')
             .replace('�', '-')
    )

    texto = re.sub(r'\s*-\s*', '-', texto)
    texto = re.sub(r'^([A-Z]+)\s*([0-9]{4})$', r'\1-\2', texto)
    texto = re.sub(r'[^A-Z0-9-]', '', texto)

    return texto


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


def limpiar_texto(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()
    texto = texto.replace('\n', ' ')
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def es_clave_valida(clave):
    if not clave:
        return False

    # patrón común tipo ABC-1234 o similar
    return bool(re.match(r'^[A-Z]{2,}-?[0-9]{3,4}$', clave))


def limpiar_dataframe_materias(df):
    df = normalizar_columnas(df)

    # quitar columnas totalmente vacías
    df = df.dropna(axis=1, how='all')

    rename_map = {}
    for col in df.columns:
        col_lower = str(col).strip().lower()

        if col_lower == 'clave':
            rename_map[col] = 'clave'
        elif col_lower in ['asignatura', 'materia', 'nombre']:
            rename_map[col] = 'nombre'
        elif col_lower == 'semestre':
            rename_map[col] = 'semestre'
        elif col_lower == 'periodo':
            rename_map[col] = 'periodo'

    df = df.rename(columns=rename_map)

    columnas_necesarias = ['clave', 'nombre', 'semestre']
    for columna in columnas_necesarias:
        if columna not in df.columns:
            raise ImportadorMateriasError(f"No se encontró la columna requerida: {columna}")

    # rellenar agrupaciones visuales del Excel
    df['semestre'] = df['semestre'].ffill()

    if 'periodo' in df.columns:
        df['periodo'] = df['periodo'].ffill()

    # limpiar campos
    df['clave'] = df['clave'].apply(normalizar_clave)
    df['nombre'] = df['nombre'].apply(limpiar_texto)

    # quitar filas vacías o basura
    df = df[
        (df['clave'] != '') &
        (df['nombre'] != '') &
        (df['clave'].str.lower() != 'nan') &
        (df['nombre'].str.lower() != 'nan')
    ].copy()

    # convertir semestre
    df['semestre_num'] = df['semestre'].apply(convertir_semestre_a_numero)

    # quedarnos solo con filas de semestre válido
    df = df[df['semestre_num'].notna()].copy()

    # filtrar claves que realmente parezcan clave académica
    df = df[df['clave'].apply(es_clave_valida)].copy()

    # excluir filas raras de bloques no académicos si hiciera falta
    # aquí de momento el filtro de semestre ya elimina gran parte del ruido

    df_final = df[['clave', 'nombre', 'semestre_num']].copy()
    df_final = df_final.rename(columns={'semestre_num': 'semestre'})

    # evitar duplicados por clave dentro de la hoja
    df_final = df_final.drop_duplicates(subset=['clave'], keep='first')

    return df_final


def analizar_hoja_excel(archivo_excel, nombre_hoja):
    try:
        df = pd.read_excel(archivo_excel, sheet_name=nombre_hoja)
        df_limpio = limpiar_dataframe_materias(df)
        return df_limpio.to_dict(orient='records')
    except ImportadorMateriasError:
        raise
    except Exception as e:
        raise ImportadorMateriasError(f"Error al analizar la hoja '{nombre_hoja}': {str(e)}")