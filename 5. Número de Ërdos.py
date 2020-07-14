import networkx as nx
import numpy as np
from tqdm import tqdm
from queue import Queue
from argparse import ArgumentParser
import pandas as pd
import os

def calculate_erdos(id, graph):
    # Identificador del autor
    author = "homepages/" + id

    # Incialización del diccionario
    erdos = {}

    # Inicialización de la cola para BFS
    q = Queue()
    q.put((author, 0))

    # BFS
    while not q.empty():
        author, erdos_no = q.get()
        
        # Comprobar que no se haya visitado
        if author not in erdos.keys():
            # Actualizar su número de Erdos
            erdos[author] = erdos_no
        
        # Añadir todos sus coautores a la cola para se explorados
        for coauthor in graph[author]['pubs'].keys():
            # Comprobar que no se haya visitado anteriormente
            if coauthor not in erdos.keys():
                # Actualizar el número de Erdos para todos sus vecinos
                q.put((coauthor, erdos_no + 1))
    
    return erdos

if __name__ == "__main__":
    arg_parser = ArgumentParser()

    # Obtenes los argumentos (id del autor)
    arg_parser.add_argument("erdos", help="ID del autor a partir del cual se calcula la distancia colaborativa", type=str)
    args = arg_parser.parse_args()

    # Directorio actual
    current_path = os.path.dirname(os.path.realpath(__file__))

    # Directorio de datos
    data_path = current_path + '/data'

    # Directorio de resultados
    results_path = current_path + '/results'
    if not os.path.exists(results_path):
        os.mkdir(results_path)

    # Carga de datos de los autores:
    try:
        graph = np.load(data_path + '/colab_graph.npy', allow_pickle=True).item()
    except FileNotFoundError:
        print("No se ha generado el grafo de colaboración. Por favor, ejecute los scrips anteriores")
    
    # Obtención de la distancia colaborativa a todos los autores y exportación a CSV
    erdos = calculate_erdos(args.erdos, graph)

    erdos_pd = pd.DataFrame.from_dict({
            i: [
                id[10:],
                graph[id]['name'],
                graph[id]['affiliation'],
                no,
                'dblp.org/pid/{:s}'.format(id[10:])
            ]
            for i, (id, no) in enumerate(sorted(erdos.items(), key=lambda author: author[1]))
        },
        orient='index',
        columns=["id", "name", "affiliation", "number", "link"])

    with open(results_path + '/erdos.csv', 'wt') as ferdos:
        erdos_pd.to_csv(ferdos, sep=';', line_terminator='\n', index=False)