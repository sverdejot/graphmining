import requests as rq
import numpy as np
from tqdm import tqdm
from modules.decoder import Decoder
from modules.scrapper import Scrapper
from modules.crawler import Crawler
from modules.graphgen import build_graph
from time import perf_counter
import os

def download_file(path):
    # Tamaño del chunk para actualizar la barra de progreso (1kB)
    chunk_size = 1024

    # Petición al servidor de dblp para descargar el volcado de la base de datos
    xml_request = rq.get('https://dblp.org/xml/dblp.xml.gz', stream=True)
    xml_path = path + '\\dblp.xml'

    total_size = int(xml_request.headers.get('content-lenght', 0))

    progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True, desc="Descargando fichero XML")
    with open(xml_path, "wb") as xml_file:
        for chunk in xml_request.iter_content(chunk_size):
            progress_bar.update(len(chunk))
            xml_file.write(chunk)
    progress_bar.close()

    # Petición al servidor para la descarga del fichero de transcripciones
    dtd_request = rq.get('https://dblp.org/xml/dblp.dtd')
    dtd_path = path + '\\dblp.dtd'

    with open(dtd_path, 'wt') as dtd_file:
        dtd_file.write(dtd_request.content.decode('utf-8'))

    return (xml_path, dtd_path)

if __name__ == "__main__":
    # Directorio actual
    current_dir = os.path.realpath(os.path.dirname(__file__))

    # Directorio donde se almacenarán los ficheros descargados y generados
    files_path = current_dir + '\\files'
    if not os.path.exists(files_path):
        os.mkdir(files_path)

    start = perf_counter()
    # Descarga del fichero
    xml_path, dtd_path = download_file(files_path)
    decoded_xml = files_path + '\\decoded-dblp.xml'

    # Decodificación del fichero
    decoder = Decoder(xml_path, decoded_xml ,dtd_path)
    decoder.recode_file()

    # Obtención de los identificadores del fichero (España)
    scrapper = Scrapper()
    ids = scrapper.scrape(decoded_xml, mask='spain')

    # Descarga de datos de los autores
    crawler = Crawler()
    authors_data = {}

    pbar = tqdm(total=len(ids), desc="Descargando datos de los investigadores")
    for id in ids:
        authors, props = crawler.crawl(id)
        # Si al descargar los datos de un autor el servidor devuelve HTTP404 (Not found) se descarta ese autor
        if props is not None:
            authors_data[id] = props
        pbar.update()
    pbar.close()

    # Generación del grafo
    graph = dict(build_graph(authors_data))

    end = perf_counter() - start
    print(" PROCESO TERMINADO. Tiempo empleado: {:d}:{:d}".format(int(round(end/60)), int(end%60)))

    data_path = current_dir + '\\data'
    if not os.path.exists(data_path):
        os.mkdir(data_path)

    graph_path = data_path + '\\colab_graph.npy'

    np.save(graph_path, graph)
    print("Se ha almacenado el grafo generado en {:s}".format(graph_path))
