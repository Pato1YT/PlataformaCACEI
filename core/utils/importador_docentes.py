import re
import pandas as pd
from unidecode import unidecode


class ImportadorDocentesError(Exception):
    pass


def obtener_hojas_excel_docentes(archivo_excel):
    try:
        excel_file = pd.ExcelFile(archivo_excel)
        return excel_file.sheet_names
    except Exception as e:
        raise ImportadorDocentesError(f"No se pudo leer el archivo Excel: {str(e)}")


def limpiar_nombre_docente(nombre):
    if pd.isna(nombre):
        return ""

    nombre = str(nombre).strip()

    if not nombre:
        return ""

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

    limpio = nombre
    for patron in patrones:
        limpio = re.sub(patron, '', limpio, flags=re.IGNORECASE)

    limpio = re.sub(r'\s+', ' ', limpio).strip()
    return limpio


def separar_nombre_apellidos(nombre_completo):
    partes = nombre_completo.split()

    if len(partes) == 1:
        return partes[0], ""

    if len(partes) == 2:
        return partes[0], partes[1]

    # heurística simple:
    # todo menos los últimos 2 tokens = nombres
    # últimos 2 tokens = apellidos
    first_name = " ".join(partes[:-2])
    last_name = " ".join(partes[-2:])

    return first_name, last_name


def generar_username_base(first_name, last_name, nombre_completo):
    if first_name or last_name:
        base_nombre = first_name.split()[0] if first_name else ""
        base_apellido = last_name.split()[0] if last_name else ""
        base = f"{base_nombre}.{base_apellido}".strip(".")
    else:
        base = nombre_completo.replace(" ", ".")

    base = unidecode(base.lower())
    base = re.sub(r'[^a-z0-9._]+', '', base)
    base = re.sub(r'\.+', '.', base).strip('.')

    return base or "docente"


def analizar_hoja_docentes(archivo_excel, nombre_hoja):
    try:
        df = pd.read_excel(archivo_excel, sheet_name=nombre_hoja)
    except Exception as e:
        raise ImportadorDocentesError(f"No se pudo leer la hoja '{nombre_hoja}': {str(e)}")

    df.columns = [str(c).strip() for c in df.columns]

    columna_docente = None
    for col in df.columns:
        if str(col).strip().lower() == 'docente':
            columna_docente = col
            break

    if not columna_docente:
        raise ImportadorDocentesError("No se encontró la columna 'Docente' en la hoja seleccionada.")

    nombres = df[columna_docente].dropna().astype(str).tolist()

    docentes_unicos = []
    vistos = set()

    for nombre in nombres:
        limpio = limpiar_nombre_docente(nombre)

        if not limpio:
            continue

        clave = limpio.lower()
        if clave in vistos:
            continue

        vistos.add(clave)

        first_name, last_name = separar_nombre_apellidos(limpio)
        username_base = generar_username_base(first_name, last_name, limpio)

        docentes_unicos.append({
            'nombre_original': nombre,
            'nombre_limpio': limpio,
            'first_name': first_name,
            'last_name': last_name,
            'username_base': username_base,
        })

    return docentes_unicos