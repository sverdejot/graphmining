import numpy as np, networkx as nx
import os
from tqdm import tqdm as tqdm
import pandas as pd
from networkx.algorithms import average_clustering, centrality
from time import perf_counter

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
    properties = {id: {'name': props['name'], 'affiliation': props['affiliation'] } for id, props in graph.items()}
    nx.set_node_attributes(network, properties)

    return network



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
    metrics['av_degree'] = (2*m)/n
    metrics['density'] = (2*m)/(n*(n-1))
    metrics['max_degree'] = getprops(max(dict(network.degree()).items(), key=lambda degree: degree[1]))

    # Distribución de probabilidad del grado
    degree_distribution = [(i, len([author for (author, degree) in network.degree() if degree == i])/len(network.nodes.data())) for i in range(max(dict(network.degree()).items(), key=lambda degree: degree[1])[1])]
    metrics['max_degree_p'] = max(degree_distribution, key=lambda degree_p: degree_p[1])

    # Coeficiente de clustering promedio
    metrics['clustering_coefficient'] = average_clustering(network)

    # Nodo con mayor centralidad promedio
    metrics['max_closeness_centrality'] = getprops(max(centrality.closeness_centrality(network).items(), key=lambda pair: pair[1]))

    return metrics

if __name__ == "__main__":
    # Directorio actual
    current_path = os.path.dirname(os.path.realpath(__file__))

    # Directorio de datos
    data_path = current_path + '\\data'

    # Directorio de resultados (aquí se exportarán los CSV)
    results_path = current_path + '\\results'
    if not os.path.exists(results_path):
        os.mkdir(results_path)

    # Carga del grafo
    try:
        graph = np.load(data_path + '\\colab_graph.npy', allow_pickle=True).item()
    except FileNotFoundError:
        print("No se ha encontrado el grafo de colaboración. Por favor, ejecute los scripts anteriores")

    # Conversión de diccionario a grafo de NetworkX
    network = build_nxGraph(graph)
    degree = {}
    a = nx.degree(network)
    for i in range(max(nx.degree(network), key=lambda pair: pair[1])[1]+1):
        degree[i] = [author for author, degree in list(nx.degree(network)) if degree == i]

    dff = pd.DataFrame([[
        degree,
        sum([nx.closeness_centrality(network, auth) for auth in authors])/len(authors),
    ]for degree, authors in degree.items() if len(authors) > 0], columns=['degree', 'closeness'])

    with open(results_path + '\\histogram_closeness.csv', 'wt') as f:
        dff.to_csv(f, line_terminator='\n', index=False)
    '''
    graph_metrics = {}

    # Cálculo de las métricas para el grafo original
    graph_metrics['Grafo original'] = calculate_metrics(network)

    # Obtención de la componente más grande y sus métricas
    largest_cc_nodes = sorted(nx.connected_components(network), key=len, reverse=True)[0]
    largest_cc = network.subgraph(largest_cc_nodes)

    graph_metrics['Máxima componente'] = calculate_metrics(largest_cc)

    # Exportación a CSV de todas las métricas obtenidas
    df_metrics = pd.DataFrame(graph_metrics).T
    with open(results_path + '\\metrics.csv', 'wt') as fmetrics:
        print("Se han exportado las métricas en: {:s}".format(results_path + '\\metrics.csv'))
        df_metrics.to_csv(fmetrics, sep=';', line_terminator='\n')

    # Función para generar el enlace a la página del autor
    gen_link = lambda id: 'dblp.org/pid/' + id

    # Obtención y exportación a CSV del listado de autores ordenados por valor de grado
    df_degree = pd.DataFrame([
                [author[10:],
                nx.get_node_attributes(network, 'name')[author],
                nx.get_node_attributes(network, 'affiliation')[author], degree,
                gen_link(author[10:])]
            for author, degree in sorted(network.degree(), reverse=True, key=lambda node: node[1])
        ],
        columns=['id', 'name', 'affiliation', 'degree', 'link'])

    with open(results_path + '\\degree.csv', 'wt') as fdegree:
        print("Se ha exportado el listado de autores ordenado por grado en: {:s}".format(results_path + '\\degree.csv'))
        df_degree.to_csv(fdegree, sep=';', line_terminator='\n', index=False)

    # Obtención y exportación a CSV de la distribución del grado ordenada por probabilidad
    df_degree_distrib = pd.DataFrame(
        sorted([
                [i,
                 len([author for (author, degree) in network.degree() if degree == i])/len(network.nodes.data()),
                 len([author for (author, degree) in network.degree() if degree == i])]
            for i in range(max(network.degree(), key=lambda degree: degree[1])[1] + 1)
        ],
        key=lambda degree: degree[1],
        reverse=True),
        columns=["deg", "P(deg)", "count"])

    with open(results_path + '\\degree_distrib.csv', 'wt') as fpdegree:
        print("Se ha exportado la distribución del grado en: {:s}".format(results_path + '\\degree_distrib.csv'))
        df_degree_distrib.to_csv(fpdegree, sep=';', line_terminator='\n', index=False)

    # Obtención y exportación a CSV del listado de autores ordenado por coeficiente de agrupamiento
    df_cclustering = pd.DataFrame([
                [author[10:],
                 nx.get_node_attributes(network, 'name')[author],
                 nx.get_node_attributes(network, 'affiliation')[author],
                 cc,
                 nx.degree(network)[author],
                 gen_link(author[10:])]
            for author, cc in sorted(nx.clustering(network).items(), key=lambda node: node[1], reverse=True)],
        columns=['id', 'name', 'affiliation', 'cc', 'degree', 'link'])

    with open(results_path + '\\clustering.csv', 'wt') as fclistering:
        print("Se ha exportado el listado de autores ordenado por coeficiente de clustering en: {:s}".format(results_path + '\\clustering.csv'))
        df_cclustering.to_csv(fclistering, sep=';', line_terminator='\n', index=False)

    # Obtención y exportación a CSV de la centralidad por cercanía
    df_closeness = pd.DataFrame([
                [author[10:],
                 nx.get_node_attributes(network, 'name')[author],
                 nx.get_node_attributes(network, 'affiliation')[author],
                 closeness,
                 gen_link(author[10:])]
            for author, closeness in sorted(nx.closeness_centrality(network).items(), reverse=True, key=lambda node: node[1])],
        columns=['id', 'name', 'affiliation', 'closeness', 'link'])

    with open(results_path + '\\closeness.csv', 'wt') as fcloseness:
        print("Se ha exportado el listado de autores ordenado por centralidad de cercanía en: {:s}".format(results_path + '\\closeness.csv'))
        df_closeness.to_csv(fcloseness, sep=';', line_terminator='\n', index=False)

    df_comp_degree_closeness = pd.DataFrame([
                [author,
                 nx.get_node_attributes(network, 'name')['homepages/' + author],
                 nx.get_node_attributes(network, 'affiliation')['homepages/' + author],
                 closeness,
                 df_degree.iloc[df_degree['id'].to_list().index(author)]['degree'],
                 list(df_degree['id']).index(author)+1,
                 gen_link(author)]
            for author, closeness in list(df_closeness[['id', 'closeness']].to_numpy())
        ],
        columns=['id', 'name', 'affiliation', 'closeness', 'degree', 'pos', 'link'])

    with open(results_path + '\\closeness_comp.csv', 'wt') as fclosenesscomp:
        print("Se ha exportado la comparación entre centralidad de cercanía y grado en: {:s}".format(results_path + '\\closeness_comp.csv'))
        df_comp_degree_closeness.to_csv(fclosenesscomp, sep=';', line_terminator='\n', index=False)

    df_betweenness = pd.DataFrame([
            [author[10:],
             nx.get_node_attributes(network, 'name')[author],
             nx.get_node_attributes(network, 'affiliation')[author],
             betweenness,
             gen_link(author[10:])]
            for author, betweenness in sorted(nx.betweenness_centrality(network).items(), key=lambda betweenness: betweenness[1], reverse=True)
        ],
        columns=['id', 'name', 'affiliation', 'betweenness', 'link'])

    with open(results_path + '\\betweenness.csv', 'wt') as fbetweenness:
        print("Se ha exportado el listado de autores ordenado por centralidad de intermediación: {:s}".format(results_path + '\\betweenness.csv'))
        df_betweenness.to_csv(fbetweenness, sep=';', line_terminator='\n', index=False)

    # Obtención de la centralidad por intermediación
    df_comp_degree_closeness = pd.DataFrame([
            [author,
             nx.get_node_attributes(network, 'name')['homepages/' + author],
             nx.get_node_attributes(network, 'affiliation')['homepages/' + author],
             betweenness,
             df_degree.iloc[df_degree['id'].to_list().index(author)]['degree'],
             list(df_degree['id']).index(author) + 1,
             gen_link(author)]
            for author, betweenness in list(df_betweenness[['id', 'betweenness']].to_numpy())
        ],
        columns=['id', 'name', 'affiliation', 'closeness', 'degree', 'pos', 'link'])

    with open(results_path + '\\betweenness_comp.csv', 'wt') as fbetweennesscomp:
        print("Se ha exportado la comparación entre centralidad de intermediación y grado en: {:s}".format(results_path + '\\betweenness_comp.csv'))
        df_comp_degree_closeness.to_csv(fbetweennesscomp, sep=';', line_terminator='\n', index=False)'''