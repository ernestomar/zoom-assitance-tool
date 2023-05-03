from unidecode import unidecode
import sys
import numpy as np
import Levenshtein
import pandas as pd


def find_similar_name(name_list, name):
    min_distance = np.inf
    similar_name = ""
    
    # Convertimos a minúsculas y eliminamos los acentos de la cadena de entrada
    name = unidecode(name.upper())
    
    # Dividimos la cadena de entrada en palabras
    name_words = name.split()

    # Verificamos que exista al menos un match current_min_distance = 0
    match_exists = False
    for n in name_list:
        # Convertimos a minúsculas y eliminamos los acentos de cada palabra en el nombre de la lista
        n_words = [unidecode(w.upper()) for w in n.split()]
        
        # Calculamos la distancia de Levenshtein para cada palabra y nos quedamos con la menor
        distances = []
        for word in name_words:
            current_min_distance = np.inf
            for list_word in n_words:
                current_distance = Levenshtein.distance(list_word, word)
                if current_distance < current_min_distance:
                    current_min_distance = current_distance
            distances.append(current_min_distance)
            if current_min_distance == 0:
                match_exists = True
        
        # Sumamos las distancias menores de cada palabra para encontrar una en total.
        if distances:
            distance = sum(distances)
        else:
            distance = np.inf
        
        # Actualizamos el nombre más similar encontrado hasta ahora si encontramos una distancia menor
        if distance < min_distance:
            min_distance = distance
            similar_name = n
    if match_exists:
        return similar_name
    else:
        return None


def load_zoom_csv(filename):
    # Carga el archivo CSV en un DataFrame de Pandas
    df = pd.read_csv(filename,
                    dayfirst=True,  # Indica que el formato de fecha es día/mes/año
                    parse_dates=['Join Time', 'Leave Time'],  # Convierte las columnas de fecha a objetos de fecha
                    dtype={'Name (Original Name)': 'string',  # Especifica el tipo de datos de cada columna
                            'User Email': 'string',
                            'Duration (Minutes)': 'int64',
                            'Guest': 'string',
                            'Recording Consent': 'string',
                            'In Waiting Room': 'string'}
    )

    # Muestra las primeras 5 filas del DataFrame
    return df


def read_students(file):
    # Abrir el archivo en modo lectura
    archivo = open(file, 'r')

    # Crear una lista vacía para almacenar las líneas del archivo
    lineas = []

    # Iterar sobre cada línea del archivo
    for linea in archivo:
        # Añadir la línea a la lista, eliminando el salto de línea al final
        name = linea.rstrip('\n')
        name = unidecode(name.upper())
        lineas.append(name)

    # Cerrar el archivo
    archivo.close()
    return lineas


def process_assistance(assistance_df, students):
    for index, row in assistance_df.iterrows():
        name = row['Name (Original Name)']
        similar_name = find_similar_name(students, name)
        # Contabilizamos los minutos participados
        if similar_name:
            joint_time = row['Join Time']
            leave_time = row['Leave Time']
            print(f"{similar_name} participó {leave_time - joint_time} minutos.")


def main(teacher_name):
    # Leemos lista de estudiantes
    students = read_students('work/students.txt')
    assistance_df = load_zoom_csv('work/2023-03-31_Sesion_1.csv')
    process_assistance(assistance_df, students)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Por favor, proporcione el nombre del profesor.")
