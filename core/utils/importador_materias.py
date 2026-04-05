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
    df.columns = [str(col).strip() for col in df.columns]
    return df


def convertir_semestre_a_numero(valor):
    if pd.isna(valor):
        return None

    texto = str(valor).strip().lower()
    match = re.search(r'(\d+)', texto)

    if match:
        return int(match.group(1))

    return None


def limpiar_dataframe_materias(df):
    df = normalizar_columnas(df)

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

    if 'semestre' in df.columns:
        df['semestre'] = df['semestre'].ffill()

    if 'periodo' in df.columns:
        df['periodo'] = df['periodo'].ffill()

    df['clave'] = df['clave'].astype(str).str.strip()
    df['nombre'] = df['nombre'].astype(str).str.strip()

    df = df[
        (df['clave'].notna()) &
        (df['nombre'].notna()) &
        (df['clave'] != '') &
        (df['nombre'] != '') &
        (df['clave'].str.lower() != 'nan') &
        (df['nombre'].str.lower() != 'nan')
    ]

    df['semestre_num'] = df['semestre'].apply(convertir_semestre_a_numero)
    df = df[df['semestre_num'].notna()]

    df_final = df[['clave', 'nombre', 'semestre_num']].copy()
    df_final = df_final.rename(columns={'semestre_num': 'semestre'})
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