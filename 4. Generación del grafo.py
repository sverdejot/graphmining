import os
import numpy as np
from collections import deque, defaultdict
from tqdm import tqdm

def build_graph(data):
    '''

    Construye el grafo a partir del listado de autores con sus publicaciones asignadascomp

    Parameters
    ----------
        data : dict
            El formato del diccionario 'data' debe ser el siguiente:

                {
                    autor1: {
                        'name': 'nombre del autor1',
                        'affiliation': 'afiliación del autor1'
                        'pubs': [publicacion1, publicacion2, publicacion3]
                    },
                    autor2: {
                        'name': 'nombre del autor2',
                        'affiliation': 'afiliación del autor2'
                        [publicacion2, publicacion4, publicacion5]
                    },
                    autor3: {
                        'name': 'nombre del autor3',
                        'affiliation': 'afiliación del autor3'
                        [publicacion2, publicacion4, publicacion6]
                    }
                }
    Returns
    -------
        graph : dict
            El formato del diccionario devuelto es el siguiente:
            
            {
                autor1: {
                    'name': 'nombre del autor1',
                    'affiliation': 'afiliación del autor1'
                    'pubs': {
                        'autor2': { 'weight': 1 },
                        'autor3': { 'weight': 1 }
                    }
                },
                autor2: {
                    'name': 'nombre del autor2',
                    'affiliation': 'afiliación del autor2'
                    'pubs': {
                        'autor1': { 'weight': 1 },
                        'autor3': { 'weight': 2 }
                },
                autor3: {
                    'name': 'nombre del autor3',
                    'affiliation': 'afiliación del autor3'
                    'pubs': {
                        'autor1': { 'weight': 1 },
                        'autor2': { 'weight': 2 }
                    }
                }
            }    
    '''

    # Copiamos el diccionario para eliminar elemento al iterar sin afectar al original
    '''
        Se elimina el autor analizado en esa iteración ya que para cada uno de sus coautores, en la lista de coautores de éstos se añade el autor en cuestión,
        eliminando una comparación innecesaria en la siguiente iteración
        
        La complejidad temporal de eliminar un elemento de un diccionario es O(1)
    '''
    data_copy = data.copy()

    # Inicializamos la cola LIFO con las claves del diccionario
    '''
        Se utiliza una cola LIFO de tal manera que al obtener el último elemento de la lista no es necesario 
        recalcular los índices del resto, por lo que la eficiencia mejora
        
        La complejidad temporal de obtener un elemento de una cola LIFO es O(1)
    '''
    deque_data = deque(list(data_copy.items()))

    # Inicializamos el diccionario devuelto
    res = defaultdict(lambda: defaultdict(dict))

    # Iteramos hasta que se hayan recorrido todos los elementos
    pbar = tqdm(total=len(deque_data))
    while len(deque_data) > 0:
        # Obtenemos la clave del final de la lista (más eficiente, no hay que recalcular índices)
        key, value = deque_data.pop()

        # Añadimos las propiedades (nombre y afiliación) al nodo
        res[key]['name'] = value['name']
        res[key]['affiliation'] = value['affiliation']

        # Si anteriormente no se ha añadido ningun autor a su lista de coautores, genera un nuevo diccionario vacío
        res[key].setdefault('pubs', {})

        # Eliminamos el autor del diccionario copia para que no se vuelva a comprobar -> todas las demás claves que estén relacionadas con ésta estarán actualizadas al finalizar la iteración
        del data_copy[key]

        # Iteramos sobre el resto de valores
        for _key, _value in data_copy.items():
            # Obtenemos el tamaño de la intersección de las listas de valores
            intersection = len(set(value['pubs'])&set(_value['pubs']))

            # Actualizamos los valores de las dos claves
            if intersection > 0:
                res[key]['pubs'][_key] = { 'weight': intersection }
                res[_key]['pubs'][key] = { 'weight': intersection }

        pbar.update()

    return {key: dict(value) for key, value in res.items()}

if __name__ == "__main__":
    data_path = os.path.dirname(os.path.realpath(__file__)) + '/data'

    authors_data = np.load(data_path + '/authors_data.npy', allow_pickle=True).item()

    graph = dict(build_graph(authors_data))

    # En caso de que un autor no tenga publicaciones en común con nadie (no tiene clave 'pubs'). Iteramos y establecemos a {}
    for author, props in graph.items():
        if 'pubs' not in props.keys():
            props['pubs'] = {}

    np.save(data_path + '/colab_graph.npy', graph)