import os
import json
import pandas as pd
import datetime

all_json = {}

def cargar_datos(ruta_archivo):
    df = pd.read_excel(ruta_archivo, header=None)
    indice_cabecera = df[df.apply(lambda row: row.astype(str).str.contains('Códigos UNSPSC').any(), axis=1)].index[0]
    df = pd.read_excel(ruta_archivo, header=indice_cabecera)
    
    return df

def limpiar_datos(df):
    # Eliminar columnas no deseadas
    columnas_a_eliminar = ['Unnamed: 0','¿Se requieren vigencias futuras?', 'Estado de solicitud de vigencias futuras','Valor estimado en la vigencia actual']
    df = df.drop(columns=columnas_a_eliminar)    
    nombres_nuevos = {
        'Códigos UNSPSC': 'Codigo',
        'Descripción': 'Descripcion',
        'Fecha estimada de inicio de proceso de selección (mes)': 'FechaInicio',
        'Duración estimada del contrato (número de mes(es))': 'Duracion',
        'Modalidad de selección': 'Modalidad',
        'Fuente de los recursos': 'Fuente',
        'Valor total estimado': 'ValorTotal',
        'Datos de contacto del responsable': 'Contacto'
    }
    df = df.rename(columns=nombres_nuevos)
    df = df.dropna(subset=['Codigo', 'Descripcion'])
    
    return df

def obtener_presupuesto_total(df):
    presupuesto_total = pd.to_numeric(df['ValorTotal'], errors='coerce').dropna().sum()
    return presupuesto_total

def obtener_maxima_cuantia(df):
    df['ValorTotal'] = pd.to_numeric(df['ValorTotal'], errors='coerce')
    indice_max_valor = df['ValorTotal'].idxmax()
    fila_max_valor = df.loc[indice_max_valor]
    return fila_max_valor

def obtener_minima_cuantia(df):
    df['ValorTotal'] = pd.to_numeric(df['ValorTotal'], errors='coerce')

    indice_min_valor = df['ValorTotal'].idxmin()
    fila_min_valor = df.loc[indice_min_valor]
    return fila_min_valor

def obtener_meses_promedio(df):
    df = df[~df['Duracion'].apply(lambda x: isinstance(x, datetime.datetime))]
    df['Duracion'] = df['Duracion'].apply(convertir_a_meses)

    df['Duracion'] = df['Duracion'].astype(float)

    promedio_duracion = df['Duracion'].mean()
    
    return promedio_duracion

def convertir_a_meses(duracion):
    duracion = str(duracion).upper()  # Convertir la duración a mayúsculas para evitar problemas
    
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


def obtener_proyectos_mas_costosos(df, cantidad=5):
    top_proyectos = df.nlargest(cantidad, 'ValorTotal')
    return top_proyectos

def obtener_prestaciones_mas_costosas(df, cantidad=5):
    # Eliminar filas con valores NaN en la columna 'Descripcion'
    df = df.dropna(subset=['Descripcion'])
    
    # Filtrar las descripciones que contienen 'PRESTACION DE SERVICIOS PROFESIONALES'
    filtro_descripcion = df['Descripcion'].str.contains("PRESTACIÓN DE SERVICIOS PROFESIONALES", case=False)
    print(filtro_descripcion)
    df_filtrado = df[filtro_descripcion]
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

    
    
    json_data = {
        carpeta: {
            archivo: {
                "proyectos_mas_costosos": proyectos_mas_costosos[['Descripcion', 'ValorTotal', 'Duracion', 'Contacto']].to_dict(orient='records'),
                "prestaciones_mas_costosas": prestaciones_mas_costosas[['Descripcion', 'ValorTotal', 'Duracion', 'Contacto']].to_dict(orient='records'),
                "maxima_cuantia": maxima_cuantia['ValorTotal'],
                "minima_cuantia": minima_cuantia['ValorTotal'],
                "promedio_meses": promedio_meses,
                "presupuesto_total": presupuesto_total
            }
        }
    }
    all_json.update(json_data)

directorio_actual = os.getcwd()

# Obtener la lista de carpetas en el directorio actual
carpetas = [nombre for nombre in os.listdir(directorio_actual) if os.path.isdir(os.path.join(directorio_actual, nombre))]

# Recorrer cada carpeta y listar los archivos dentro de ella
for carpeta in carpetas:
    ruta_carpeta = os.path.join(directorio_actual, carpeta)
    archivos = [nombre for nombre in os.listdir(ruta_carpeta) if os.path.isfile(os.path.join(ruta_carpeta, nombre))]
    for archivo in archivos:
        ruta_relativa = os.path.relpath(os.path.join(ruta_carpeta, archivo), directorio_actual)
        print(ruta_relativa)
        generar_json(ruta_relativa)

# Imprimir el JSON generado
print(json.dumps(all_json, indent=4))
