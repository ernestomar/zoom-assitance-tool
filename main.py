from unidecode import unidecode
import sys
import numpy as np
import Levenshtein
import pandas as pd


def find_similar_name(participant_list, name):
    index = -1
    min_distance = np.inf
    similar_name = ""
    
    # Convertimos a minúsculas y eliminamos los acentos de la cadena de entrada
    name = unidecode(name.upper())
    
    # Dividimos la cadena de entrada en palabras
    name_words = name.split()

    # Verificamos que exista al menos un match current_min_distance = 0
    match_exists = False
    for idx, participant in enumerate(participant_list):
        # Convertimos a minúsculas y eliminamos los acentos de cada palabra en el nombre de la lista
        n_words = [unidecode(w.upper()) for w in participant['name'].split()]
        
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
                index = idx
        
        # Sumamos las distancias menores de cada palabra para encontrar una en total.
        if distances:
            distance = sum(distances)
        else:
            distance = np.inf
        
        # Actualizamos el nombre más similar encontrado hasta ahora si encontramos una distancia menor
        if distance < min_distance:
            min_distance = distance
            similar_name = participant
    if match_exists:
        return index
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


def process_assistance(assistance_df, participants):
    print(f"Procesando asistencia...")
    for index, row in assistance_df.iterrows():
        name = row['Name (Original Name)']
        match_index = find_similar_name(participants, name)
        # Contabilizamos los minutos participados
        if match_index is not None:
            # Si ya tiene una lista de conecciones
            if 'connections' in participants[match_index]:
                participants[match_index]['connections'].append({'join_time': row['Join Time'],
                                                                 'leave_time': row['Leave Time']})
            else:
                participants[match_index]['connections'] = [{'join_time': row['Join Time'],
                                                             'leave_time': row['Leave Time']}]
    return participants

def get_first_teacher(lista):
    for diccionario in lista:
        if diccionario["teacher"]:
            return diccionario
    return None


# Buscamos la hora de entrada más temprana y la hora de salida más tardía
def get_earliest_join_latest_leave(data):
    join_times = [conn['join_time'] for conn in data['connections']]
    leave_times = [conn['leave_time'] for conn in data['connections']]
    earliest_join_time = min(join_times)
    latest_leave_time = max(leave_times)
    return earliest_join_time, latest_leave_time


from datetime import datetime, timedelta


# Primero, se debe asegurar que las marcas de tiempo (timestamps) estén en un formato que Python pueda entender.
# Dado que estas parecen estar en formato de cadena de texto (string), deberías convertirlas a objetos datetime.
# Para ello, puedes utilizar el módulo datetime en Python.
#
# A continuación, proporciono una posible implementación de la función que has descrito.
# Esta función primero ordena las conexiones por join_time, luego recorre cada conexión, y si hay algún solapamiento,
# ajusta el tiempo de inicio de la conexión actual al tiempo de finalización de la conexión anterior.
# Después, se calcula el tiempo total de participación.
def calculate_participation(student_dict, session_init, session_end):
    if 'connections' not in student_dict:
        return 0

    # Ordenar las conexiones por join_time
    connections = sorted(student_dict['connections'], key=lambda x: x['join_time'])
    computed_connections = []
    for idx, connection in enumerate(connections):
        # Si join_time es anterior a session_init, ajustar join_time a session_init
        if connection['join_time'] < session_init:
            connection['join_time'] = session_init
        # Si leave_time es posterior a session_end, ajustar leave_time a session_end
        if connection['leave_time'] > session_end:
            connection['leave_time'] = session_end

        # La primera conexion entra tal cual
        if idx == 0:
            computed_connections.append(connection)
        else:
            # Si la conexion actual se superpone con la anterior, se ajusta el tiempo de inicio de la conexion actual
            if connection['join_time'] < computed_connections[-1]['leave_time']:
                connection['join_time'] = computed_connections[-1]['leave_time']
                # Si el tiempo de inicio de la conexion actual es posterior al tiempo de finalizacion
                # de la conexion actual
                if connection['join_time'] > connection['leave_time']:
                    continue
                else:
                    computed_connections.append(connection)
            else:
                computed_connections.append(connection)

    # Calcular el porcentaje de tiempo de participación
    session_duration = session_end - session_init

    total_participation = timedelta(0)
    for connection in computed_connections:
        total_participation += connection['leave_time'] - connection['join_time']

    participation_percentage = (total_participation.total_seconds() / session_duration.total_seconds()) * 100

    return participation_percentage


def main(teacher_name):
    # Leemos lista de estudiantes
    students = read_students('work/students.txt')
    # Agregamos al profesro como primer elemento
    students.insert(0, teacher_name)
    # Convertimos la lista de cadenas a una lista de diccionarios.
    participant_list = []

    for i, item in enumerate(students):
        participant = {
            "name": item,
            "teacher": True if i == 0 else False
        }
        participant_list.append(participant)

    # Cargamos la planilla de asistencia
    assistance_df = load_zoom_csv('work/2023-03-31_Sesion_1.csv')
    participants = process_assistance(assistance_df, participant_list)

    teacher = get_first_teacher(participants)
    class_time = get_earliest_join_latest_leave(teacher)
    print("El horario de la clase fue de {} a {}".format(class_time[0], class_time[1]))
    for student in participants:
        participation = calculate_participation(student, class_time[0], class_time[1])
        print("El estudiante {} participó el {}% del tiempo".format(student["name"], participation))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Por favor, proporcione el nombre del profesor.")
