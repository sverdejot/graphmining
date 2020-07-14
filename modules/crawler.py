from urllib3 import HTTPSConnectionPool
from lxml import etree
import numpy as np
from time import sleep
from tqdm import trange, tqdm
from io import BytesIO
from argparse import ArgumentParser
import re
import os

http = HTTPSConnectionPool(host="dblp.org", maxsize=400)

current_path = os.path.dirname(os.path.realpath(__file__))

class Crawler:
    '''
    Módulo encargado de descargar del servidor todos los datos de los autores.

    Al no estar asociados en el volcado de la base de datos los identifcadores de las publicaciones a los identificadores de sus autores
    se deben descargar éstos individualmente y asociarlos al identificador del autor.

    dblp limita el número de peticiones por minuto, por lo que es necesario establecer un control. Este módulo gestiona automáticamente
    el límite de peticiones, realizando las máximas posibles hasta que recibe HTTP429 Max retries.

    Como mencionan en su F.A.Q., la respuesta del servidor incluye un parámetro 'Retry-After', que determina el tiempo que debe esperar el
    script para continar con la descarga

    Si recibe HTTP404, la página no ha sido encontrada por lo que el autor se descarta
    '''
    def __init__(self):
        self.http = HTTPSConnectionPool(host="dblp.org", maxsize=400)

    def crawl(self, author):
        '''
            Método para descargar la página en formato XML del servidor

            Parameters
            ----------
                author : str
                    identificador del autor del que se va a descargar la página

            Returns
            -------
                (author, props) : (str, dict)
                    Propiedades del autor (nombre, afiliación y publicaciones) asociadas al identificador

        '''
        page = self.http.request('GET', '/pid' + author[9:] + '.xml')
        
        # En caso de que el status code de la respuesta sea HTTP200 (Success) procesa la página para obtener las publicaciones
        if page.status == 200:
            return (author, self.parse_XML(page.data))
        # En caso de que sea HTTP429 (Max retries) espera el tiempo establecido por el servidor para volver a enviar peticiones
        elif page.status == 429:
            for _ in trange(int(page.headers['Retry-After']), desc="Máximo de peticiones alcanzado"):
                sleep(1)
            return self.crawl(author)
        # En casos de que sea HTTP404 (Not found) no se ha encontrado la página del autor, por que lo devuelve None publicaciones
        elif page.status == 404:
            return (author, None)
        # En cualquier otro caso, lanza una excepción no controlada
        else:
            raise Exception("ERROR (status code: " + str(page.status) + ")")

    def parse_XML(self, page):
        '''

        Parameters
        ----------
            page : str
                página personal del autor en formato XML

        Returns
        -------
            props : dict
                Propiedades del autor (nombre, afiliación y publicaciones) obtenidas de la página

        '''

        pubs = []
        xml = etree.iterparse(BytesIO(page), events=('start', 'end'))

        # Inicalización de los valores
        name = None
        affiliation = None
        for event, publ in xml:
            if event == "start":
                if publ.tag == 'dblpperson':
                    name = publ.get('name')
                    note = publ.find('person').find('note')
                    if note.get('type') == 'affiliation':
                        affiliation = note.text
                if publ.tag == 'r':
                    try:
                        pubs.append(publ[0].get('key'))
                    except:
                        pass
        return {"name": re.sub(r'\s[0-9]+', '',  name), "affiliation": affiliation, "pubs": pubs}

if __name__ == "__main__":
    arg_parser = ArgumentParser()

    # Obtención de los argumentos
    arg_parser.add_argument("--mask", action="store", help="Máscara que se ha aplicado para obtener los IDs", default=None, choices=["spain", "uclm"])

    args = arg_parser.parse_args()

    # Directorio actual
    current_path = os.path.dirname(os.path.realpath(__file__))

    # Directorio de datos
    data_path = current_path + '/data'

    # Fichero de IDs
    filename = data_path + "/{:s}-ids.txt".format(args.mask)

    # Inicialización del diccionario donde se almacenarán los datos
    auhtors_data = {}

    crawler = Crawler()

    # Lista de identificadores
    with open(filename) as data_file:
        data = data_file.read().splitlines()
    
    # Inicialización del diccionarios de autores
    authors_data = {}

    # Descarga de los datos
    for id in tqdm(data, desc="Procesando investigadores"):
        author, props = crawler.crawl(id)
        # None si HTTP404
        if props is not None:
            authors_data[author] = props

    np.save(data_path + '/authors_data.npy', authors_data)