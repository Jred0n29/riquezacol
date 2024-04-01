import os
import re
import datetime
import pandas as pd


all_json = {}

def cargar_datos(ruta_archivo):
    df = pd.read_excel(ruta_archivo, header=None)
    patron = re.compile(r'c[oóÓ]digos?\s+unspsc', re.IGNORECASE)
    indice_cabecera = df[df.apply(lambda row: row.astype(str).str.contains(patron).any(), axis=1)].index[0]
    df = pd.read_excel(ruta_archivo, header=indice_cabecera)
    return df

def limpiar_datos(df):
    #Editar esta parte por lo del contacto
    columnas_a_eliminar = [0,5,6,8,9,10]
    df = df.drop(columns=df.columns[columnas_a_eliminar])
    df.columns = range(df.shape[1])

    
    nuevos_nombres = {
        0: 'Codigo',
        1: 'Descripcion',
        2: 'FechaInicio',
        3: 'Duracion',
        4: 'ValorTotal',
        5: 'Contacto'
    }
    df = df.rename(columns=nuevos_nombres)
    df = df.dropna(subset=['Codigo', 'Descripcion'])
    return df

def limpiar_nan(df):
    # Eliminar filas con valores NaN en cualquier columna
    df = df.dropna()
    return df
    
def obtener_presupuesto_total(df):
    presupuesto_total = pd.to_numeric(df['ValorTotal'], errors='coerce').dropna().sum()
    return presupuesto_total

def obtener_maxima_cuantia(df):
    # Convertir 'ValorTotal' a numérico, ignorando los errores
    df['ValorTotal'] = pd.to_numeric(df['ValorTotal'], errors='coerce')
    
    # Eliminar filas con valores nulos en 'ValorTotal'
    df = df.dropna(subset=['ValorTotal'])

    # Si hay filas después de eliminar valores nulos
    if not df.empty:
        # Calcular el índice del valor máximo en 'ValorTotal'
        indice_max_valor = df['ValorTotal'].idxmax()
        # Obtener la fila correspondiente al valor máximo
        fila_max_valor = df.loc[indice_max_valor]
        return fila_max_valor
    else:
        # Si el DataFrame está vacío después de eliminar valores nulos, retornar None en lugar de 0
        return None


def obtener_minima_cuantia(df):
    # Convertir 'ValorTotal' a numérico, ignorando los errores
    df['ValorTotal'] = pd.to_numeric(df['ValorTotal'], errors='coerce')
    df = df.dropna(subset=['ValorTotal'])

    if not df.empty:
        fila_min_valor = df.loc[df['ValorTotal'].idxmin()]
      
        return fila_min_valor
    else:
        # Si el DataFrame está vacío después de eliminar valores nulos, retornar None
        return pd.DataFrame(columns=df.columns)


def obtener_meses_promedio(df):
    df = df[~df['Duracion'].apply(lambda x: isinstance(x, datetime.datetime))]
    df['Duracion'] = df['Duracion'].apply(convertir_a_meses)

    df['Duracion'] = df['Duracion'].astype(float)

    promedio_duracion = df['Duracion'].mean()
    
    return promedio_duracion

def convertir_a_meses(duracion):
    duracion = str(duracion).upper()  # Convertir la duración a mayúsculas para evitar problemas
    try:
        if 'MES' in duracion:
            return int(duracion.split()[0])  # Tomar el número antes de 'MES'
        elif 'DIA' in duracion:
            return int(duracion.split()[0]) / 30  # Convertir días a meses (aproximadamente 30 días por mes)
        elif 'SEMANA' in duracion:
            return int(duracion.split()[0]) / 4  # Convertir semanas a meses (aproximadamente 4 semanas por mes)
        else:
            # Resto de los casos
            m = {
                'ENERO': 1,
                'FEBRERO': 2,
                'MARZO': 3,
                'ABRIL': 4,
                'MAYO': 5,
                'JUNIO': 6,
                'JULIO': 7,
                'AGOSTO': 8,
                'SEPTIEMBRE': 9,
                'OCTUBRE': 10,
                'NOVIEMBRE': 11,
                'DICIEMBRE': 12
            }
            if duracion.endswith(' M'):
                return int(duracion.split()[0])  # Tomar el número antes del espacio
            elif duracion in m:
                return m[duracion]
            else:
                return 0
    except: return 0

def obtener_proyectos_mas_costosos(df, cantidad=5):
    top_proyectos = df.nlargest(cantidad, 'ValorTotal')
    return top_proyectos

def obtener_prestaciones_mas_costosas(df, cantidad=5):
    # Eliminar filas que contienen valores NaN en cualquier columna
    df = df.dropna()

    # Filtrar las filas que contienen la cadena "PRESTACIÓN DE SERVICIOS PROFESIONALES" en la columna 'Descripcion'
    filtro_descripcion = df['Descripcion'].str.contains("PRESTACIÓN DE SERVICIOS PROFESIONALES", case=False)
    df_filtrado = df[filtro_descripcion]

    # Eliminar filas que contienen valores NaN en la columna 'ValorTotal'
    df_filtrado = df_filtrado.dropna(subset=['ValorTotal'])    

    # Obtener las 'cantidad' filas con los valores más altos en la columna 'ValorTotal'
    top_prestaciones = df_filtrado.nlargest(cantidad, 'ValorTotal')
    
    return top_prestaciones




# Función para generar el JSON
def generar_json(ruta_archivo):
    # Obtener el nombre del archivo y de la carpeta
    carpeta, archivo = os.path.split(ruta_archivo)
    carpeta = os.path.basename(carpeta)
    
    # Cargar y limpiar los datos
    df = cargar_datos(ruta_archivo)
    df = limpiar_datos(df)

    # Obtener la información requerida
    presupuesto_total = obtener_presupuesto_total(df)
    maxima_cuantia = obtener_maxima_cuantia(df)
    minima_cuantia = obtener_minima_cuantia(df)
    promedio_meses = obtener_meses_promedio(df)
    proyectos_mas_costosos = obtener_proyectos_mas_costosos(df)
    prestaciones_mas_costosas = obtener_prestaciones_mas_costosas(df)

    # Crear el diccionario JSON
    json_data = {
        carpeta: {
            archivo: {
                "proyectos_mas_costosos": proyectos_mas_costosos[['Descripcion', 'ValorTotal', 'Duracion', 'Contacto']].to_dict(orient='records'),
                "prestaciones_mas_costosas": prestaciones_mas_costosas[['Descripcion', 'ValorTotal', 'Duracion', 'Contacto']].to_dict(orient='records'),
                "maxima_cuantia": maxima_cuantia['ValorTotal'] if maxima_cuantia is not None else None,
                "minima_cuantia": minima_cuantia['ValorTotal'],
                "promedio_meses": promedio_meses,
                "presupuesto_total": presupuesto_total
            }
        }
    }
    all_json.update(json_data)


directorio_actual = os.getcwd()

# Obtener la lista de carpetas en el directorio actual
carpetas = [nombre for nombre in os.listdir(directorio_actual) if os.path.isdir(os.path.join(directorio_actual, nombre)) and ".git" not in nombre]

# Recorrer cada carpeta y listar los archivos dentro de ella
for carpeta in carpetas:
    ruta_carpeta = os.path.join(directorio_actual, carpeta)
    archivos = [nombre for nombre in os.listdir(ruta_carpeta) if os.path.isfile(os.path.join(ruta_carpeta, nombre))]
    for archivo in archivos:
        ruta_relativa = os.path.relpath(os.path.join(ruta_carpeta, archivo), directorio_actual)
        print(ruta_relativa)
        generar_json(ruta_relativa)
import json
import numpy as np

# Convertir los valores de int64 a tipos nativos de Python antes de guardar
all_json_converted = json.loads(json.dumps(all_json, default=lambda o: int(o) if isinstance(o, np.int64) else str(o)))

# Nombre del archivo de salida
nombre_archivo = 'datos.json'

# Ruta completa del archivo de salida en el directorio actual
ruta_salida = os.path.join(directorio_actual, nombre_archivo)

# Guardar el diccionario 'all_json_converted' en un archivo JSON en el directorio actual
with open(ruta_salida, 'w') as archivo_salida:
    json.dump(all_json_converted, archivo_salida, indent=4)

print(f"Archivo guardado exitosamente en: {ruta_salida}")
