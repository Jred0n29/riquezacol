import os

# Directorio actual
directorio_actual = os.getcwd()

# Obtener la lista de carpetas en el directorio actual
carpetas = [nombre for nombre in os.listdir(directorio_actual) if os.path.isdir(os.path.join(directorio_actual, nombre))]

# Recorrer cada carpeta y listar los archivos dentro de ella
for carpeta in carpetas:
    ruta_carpeta = os.path.join(directorio_actual, carpeta)
    archivos = [nombre for nombre in os.listdir(ruta_carpeta) if os.path.isfile(os.path.join(ruta_carpeta, nombre))]
    for archivo in archivos:
        ruta_relativa = os.path.relpath(os.path.join(ruta_carpeta, archivo), directorio_actual)
        print(f"{ruta_relativa}")
