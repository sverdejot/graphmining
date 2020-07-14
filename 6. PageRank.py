import numpy as np
import networkx as nx
import pandas as pd
import os

def pagerank(authors, d=0.85, alpha=0.0005):
    '''
    Devuelve un diccionario que contiene la ID de cada autor y su valor de PageRank asociado

    Parameters
    ----------
        authors_dict : dict
            diccionario formado por las IDs de los autores como clave y como valor asociado las IDs de sus coautores

        d : float
            factor de amortiguamiento. Es configurable (a pesar que en la presentación de Google recomiendan establecerlo a 0.85)
    
        alpha : float
            mínimo cambio que debe sufrir la media de los valores de PageRank de los autores en esa iteración para determinar que no ha convergido
    
    Returns
    -------

        pagerank : dict
            diccionario formado por las IDs de los autores como clave y su valor de PageRank como valor asociado
    
    '''
    # Valor inicial de PR para cada autor
    init_pr = 1/len(authors.keys())

    # Suma total de pesos
    total_weight = 0
    for props in authors.values():
        for coauthor in props['pubs'].values():
            total_weight += coauthor['weight']
    #total_weight = sum([sum(coauthor['weight'] for coauthor in props['pubs']) for props in authors.values()])

    # Inicialización de los valores de PR para cada author
    pagerank = {author: {'name': props['name'], 'affiliation': props['affiliation'], 'pr': init_pr} for author, props in authors.items()}

    convergence = False

    # Mientras no se cumpla la condición de convergencia+
    while not convergence:
        threshold = 0

        # Antes de actualizar valores, obtenemos una copia de la última iteración para generar los nuevos a partir de la última iteración
        last_pagerank = pagerank.copy()
        
        # Para cada uno de los autores y su valor de PageRank
        for author, props in pagerank.items():
            # Obtenemos la lista de coautores (nº de autores con los que se enlaza)
            coauthors = authors[author]['pubs']

            # Inicializamos el valor de PageRank para el autor y la iteración actual
            sum_pr = 0
            sum_w = 0

            # Para cada uno de los coautores 
            for coauthor, weight in coauthors.items():
                # Obtenemos la suma de pesos para este autor
                sum_w += weight['weight']

                # Obtener su valor de PageRank actual y añadirlo al nuevo valor de PageRank del autor
                sum_pr += last_pagerank[coauthor]['pr']/len(authors[coauthor]['pubs'])

            # Una vez recorrida toda la lista de coautores, actualizar el valor de PageRank del autor
            new_pr = (1-d)*(sum_w/total_weight) + (d * sum_pr)
            pagerank[author]['pr'] = new_pr

            # Añadir al umbral de esta itereación el cambio en el valor de PageRank
            threshold += abs(props['pr'] - new_pr)

        # Calcular la condición de convergencia: si la media del cambio ocurrido en los valores de PageRank para todos los autores es inferior a alpha, se considera que el algoritmo ha convergido
        convergence = threshold/len(authors.keys()) < alpha

    return pagerank

if __name__ == "__main__":
    # Directorio actual
    current_path = os.path.dirname(os.path.realpath(__file__))

    # Directorio de datos
    data_path = current_path + '\\data'

    # Directorio de resultados
    results_path = current_path + '\\results'

    if not os.path.exists(results_path):
        os.mkdir(results_path)

    # Carga del grafo
    try:
        graph = np.load(data_path + '\\colab_graph.npy', allow_pickle=True).item()
    except FileNotFoundError:
        print("No se ha generado el grafo de colaboración. Por favor, ejecute los scripts anteriores")

    # Obtención de los valores de PR
    pagerank = pagerank(graph)

    # Conversión a Pandas DataFrame y exportación a CSV
    pagerank_df = pd.DataFrame.from_dict({
            i: [
                author[10:],
                props['name'],
                props['affiliation'],
                props['pr'],
                'dblp.org/pid/{:s}'.format(author[10:])
            ]
            for i, (author, props) in enumerate(sorted(list(pagerank.items()), reverse=True, key=lambda author_pr: author_pr[1]['pr']))
        },
        orient='index',
        columns=['id', 'name', 'affiliation', 'pr', 'link'])

    with open(results_path + '\\pagerank.csv', 'wt') as fpr:
        pagerank_df.to_csv(fpr, sep=";", line_terminator='\n', index=False)