from community import best_partition
import networkx as nx
from networkx.algorithms import average_clustering, centrality
import numpy as np
import pandas as pd
import os


def build_nxGraph(graph):
    '''
    Devuelve el grafo pasado como diccionario como nx.Graph con las propiedades añadidas

    Parameters
    ----------
        graph : dict
            diccionario que tiene el formato:
            {
                autor: {
                    'name': 'nombre del autor',
                    'affiliation': 'afiliación del autor'
                    'pubs': {
                        coautor: { 'weight': int },
                        ...
                    }
                }...
            }

    Returns
    -------
        network : nx.Graph
            grafo en formato NetworkX
    '''
    # Generamos el grafo
    network = nx.Graph({author: props['pubs'] for author, props in graph.items()})

    # Añadimos las propiedades de nombre y afiliación
    properties = {id: {'name': props['name'], 'affiliation': props['affiliation']} for id, props in graph.items()}
    nx.set_node_attributes(network, properties)

    return network

def louvain_communties(G):
    '''
    Obtiene el conjunto de mejores particiones posibles para el grafo G con el algoritmo de Louvain basado en modularidad

    Parameters
    ----------
        G : nx.Graph
            red de la que se quiere obtener las particiones    
    Returns
    -------

        partitions : list
            lista de listas de los nodos de cada partición
    
    '''
    # Aplicamos el algoritmo de louvain
    partition = best_partition(G)

    # Agrupamos los nodos en listas según su partición
    communties = {}
    for node, community in partition.items():
        communties.setdefault(community, []).append(node)

    return list(communties.values())


def calculate_metrics(network):
    '''
    Calcula las métricas más importantes sobre la red y las devuelve en forma de diccionario

    Parameters
    ----------
        network : nx.Graph
            Red de la que se quiere calcular las metricas 

    Returns
    -------
        metrics : dict
            Diccionario que almacena las métricas para la red pasada por parámetro
    '''

    # Incialización del diccionario que almacena las métricas
    metrics = {}

    # Obtenemos los nombres y afiliaciones de la red
    names = nx.get_node_attributes(network, 'name')
    affiliation = nx.get_node_attributes(network, 'affiliation')

    # Función para obtener el nombre en una tupla
    getprops = lambda author_tuple: (names[author_tuple[0]], affiliation[author_tuple[0]], author_tuple[1])

    # Número de nodos y aristas
    n = len(network.nodes.data())
    m = len(network.edges.data())

    metrics['n'] = n
    metrics['m'] = m

    # Tamaño total de la red (suma de pesos)
    metrics['size'] = network.size(weight='weight')

    # Grado promedio, densidad y grado máximo
    metrics['av_degree'] = round((2 * m) / n, 5)
    metrics['density'] = (2 * m) / (n * (n - 1))
    metrics['max_degree'] = getprops(max(dict(network.degree()).items(), key=lambda degree: degree[1]))[0]

    # Distribución de probabilidad del grado
    degree_distribution = [
        (i, len([author for (author, degree) in network.degree() if degree == i]) / len(network.nodes.data())) for i in
        range(max(dict(network.degree()).items(), key=lambda degree: degree[1])[1])]
    metrics['max_degree_p'] = max(degree_distribution, key=lambda degree_p: degree_p[1])[0]

    # Coeficiente de clustering promedio
    metrics['clustering_coefficient'] = average_clustering(network)

    # Nodo con mayor centralidad promedio
    metrics['max_closeness_centrality'] = getprops(
        max(centrality.closeness_centrality(network).items(), key=lambda pair: pair[1]))[0]

    return metrics

if __name__ == "__main__":
    # Directorio actual
    current_path = os.path.dirname(os.path.realpath(__file__))

    # Directorio de datos
    data_path = current_path + '/data'

    # Directorio de resultados
    results_path = current_path + '/results'

    graph_metrics = {}

    # Carga del grafo
    try:
        graph = np.load(data_path + '/colab_graph.npy', allow_pickle=True).item()
    except FileNotFoundError:
        print("No se ha encontrado el grafo de colaboración. Por favor, ejecute los scripts anteriores")

    network = build_nxGraph(graph)

    largest_cc = nx.subgraph(network, sorted(nx.connected_components(network), key=len, reverse=True)[0])
    # Detección de comunidades y sus métricas con el algoritmo de Clauset-Newman-Moore
    for i, community in enumerate(sorted(louvain_communties(largest_cc), reverse=True, key=len)):
        cm = nx.subgraph(network, list(community))
        graph_metrics['Comunidad ' + str(i)] = calculate_metrics(cm)

    # Exportación a CSV
    df_metrics = pd.DataFrame(graph_metrics).T

    df_metrics['n'].astype(np.float)
    df_metrics['m'] = pd.to_numeric(df_metrics['m'])
    df_metrics['size'] = pd.to_numeric(df_metrics['size'])
    df_metrics['av_degree'] = pd.to_numeric(df_metrics['av_degree'])
    df_metrics['density'] = pd.to_numeric(df_metrics['density'])
    df_metrics['clustering_coefficient'] = pd.to_numeric(df_metrics['clustering_coefficient'])
    print(df_metrics[['size', 'av_degree', 'density', 'clustering_coefficient']].describe())
    nx.write_gexf(network, results_path + '/prueba.gefx')
        #df_m.to_csv(fcommunities, sep=';', line_terminator='\n')