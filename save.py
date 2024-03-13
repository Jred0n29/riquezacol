import os
import requests
import pandas as pd
import time

def descargar_archivo(url, ruta_archivo, departamento, municipio):
    response = requests.post(url, data={'ruta': ruta_archivo})
    
    if response.status_code == 200:
        tipo_mime = response.headers.get('content-type')
        if str(tipo_mime) == "application/vnd.ms-excel":
            departamento_folder = f"./{departamento}"  
            if not os.path.exists(departamento_folder):  
                os.makedirs(departamento_folder)  
            ruta_save = f"{departamento_folder}/{municipio}.xls"
            with open(ruta_save, "wb") as archivo:
                archivo.write(response.content)
            print(f"Archivo descargado exitosamente: {departamento} -- {municipio}")
            return True
    return False

def descargar_archivo_html_variaciones(url, ruta_base, departamento, municipio):
    for i in range(1,3):
        ruta_archivo = f"{ruta_base}_v{i}.xls"
        if descargar_archivo(url, ruta_archivo, departamento, municipio):
            return True
    return False

def procesar_archivos(df):
    ano = '2020'
    trimestre = '2020Q2'
    tipo_dato = 'PAA'
    ano_archivo = '2024'
    url = "https://www.contratos.gov.co/consultas/VerDocumento"

    for _, row in df.iterrows():
        codigo = str(row['Codigo'])
        datos = codigo[1:6]
        departamento = row["Departamento"]
        municipio = row["Municipio"]
        if departamento == "Antioquia":
            datos = datos[1:5]
        ruta_base = f"/{ano}/{trimestre}/{tipo_dato}/{ano_archivo}/{codigo}/{datos}/UNICO PLAN/PAA_{codigo}_{datos}"
        #if not descargar_archivo(url, ruta_base + '.xls', departamento, municipio):
        if not descargar_archivo_html_variaciones(url, ruta_base, departamento, municipio):
            print("No se pudo descargar el archivo:", departamento, "--", municipio)

        time.sleep(8)
# Leer el archivo txt
df = pd.read_csv('datos.txt', sep='\t')

# Procesar los archivos
procesar_archivos(df)
