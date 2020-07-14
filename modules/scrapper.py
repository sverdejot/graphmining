#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from lxml import etree
from tqdm import tqdm
import argparse
import os

class Scrapper:
    '''
    MÃ³dulo encargado de la extracción de los datos de la base de datos completa de dblp. Hace usos de la estructura del archivo xml para obtener los autores
    cuya afiliación (en el caso de estar especificada) sea reconocida por una de las expresiones regulares especificadas (España, UCLM o todo el mundo).
    La estructura que tienen los nodos asociados a los autores es la siguiente:

        <www mdate="2019-01-10" key="homepages/54/4230">
            <author>José A. Gámez 0001</author>
            <author>JosÃ© Antonio GÃ¡mez</author>
            <title>Home Page</title>
            <url>https://scholar.google.com/citations?user=aIvQfzUAAAAJ</url>
            <url>https://orcid.org/0000-0003-1188-1117</url>
            <note type="affiliation">University of Castilla-La Mancha, Spain</note>
        </www>

    En el caso de dblp, sólo la id asociada a las páginas específicas de cada autor son únicas y unívocas, además de no ser transitorias (como las ofrecidas
    por la API). Además, esta ID nos permitirá buscar posteriormente sus publicaciones

    Una vez ha recorrido todo el documento, escribe en el archivo especificado por parámetro todas las cuales cumplían con la condición

    Para poder identificar los autores que pertenezcan a universidades españolas pero que en su afiliación no contengan la palabra "España" o "Spain", en primer lugar
    se recorrerá el documento para obtener todas las afiliaciones que sí la contienen y, una vez hecho esto, volver a recorrer el documento comprobando si la afiliación de cada autor a pesar
    de no tener la palabra España sÃ­ se trata de una universidad española. De esta forma, si la afiliación de un autor es "University of Málaga" y la primera vez que se ha recorrido el archivo
    se ha recuperado la afiliación "University of Málaga, Spain" para cualquier otro autor, el primero también quedará almacenado en la lista.

    '''
    def __init__(self):
        self.masks = {
            "uclm" : re.compile(r'((C|c)astilla( |-)(L|l)a (M|m)ancha)|((U|u)(C|c)(L|l)(M|m))'),
            "spain" : re.compile(r'.*, (Spain|España|Espana)'),
        }

    def scrape(self, xml_path, mask=None):
        '''
        MÃ©todo encargado de recorrer el documento

        Parameters
        ----------
            xml_path : str
                directorio del archivo fuente XML (descomprimido)

            mask: re.compile()
                patron de búsqueda empleado para la aficiliación

        Attributes
        ----------
            context : str
                atributo donde se almacena el directorio fuente

            dst : str
                atributo donde se almacena el directorio de destino

            dtd : str
                atributo donde se almacena el directorio del archivo de especificacion de tipos

            entity_re : re.compile()
                expresion regular que nos permite dividir una cadena en palabras

            replacements : dict
                diccionario con las entidades especificadas en el DTD para hacer la transcripcion de ISO a UTF-8
        '''   
        
        # En caso de que se aplique una máscara (comprueba si la palarba "España/Spain" o "Universidad de Castilla-La Mancha" se encuentra en el grafo)
        if mask is not None:
            # Primer recorrido -> obtener afiliaciones
            context = etree.iterparse(xml_path, events=("start", "end"))

            affiliations = set()

            for event, url in tqdm(context, desc="Obteniendo afiliaciones"):
                if event == 'start':
                    if url.tag == 'www':
                        if url.find('note') != None:
                            note = url.find('note')
                            if note.get('type') == "affiliation" and note.text is not None:
                                if re.search(self.masks[mask], note.text):
                                    if note.text not in affiliations:
                                        affiliations.add(note.text)
                url.clear()
                while url.getprevious() is not None:
                    del url.getparent()[0]

        # Segunda iteración en caso de máscara aplicada, obtener IDs de autores
        context = etree.iterparse(xml_path, events=("start", "end"))
        ids = []

        for event, url in tqdm(context, desc="Obteniendo identificadores"):
            if event == 'start':
                if url.tag == 'www':
                    if mask is not None:
                        if url.find('note') != None:
                            note = url.find('note')
                            if note.get('type') == "affiliation" and note.text is not None:
                                if any([note.text in affiliation for affiliation in list(affiliations)]):
                                    ids.append(url.get('key'))
                    else:
                        if re.search(r'homepages\/[a-zA-Z0-9_\/]+', url.get('key')):
                            ids.append(url.get('key'))                      
            url.clear()
            while url.getprevious() is not None:
                del url.getparent()[0]

        return ids

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()

    # ObtenciÃ³n de los argumentos
    arg_parser.add_argument("xml_path", help="Ubicación del fichero XML decodificado (descomprimido)", type=str)
    arg_parser.add_argument("--mask", action="store", help="Máscara a aplicar para obtener (opcional)", default=None, choices=["spain", "uclm"])

    args = arg_parser.parse_args()

    # InstanciaciÃ³n del scrapper
    sc = Scrapper()

    authors_ids = sc.scrape(xml_path=args.xml_path, mask=args.mask)

    # Directorio actual para almacenar las IDs
    data_path = os.path.dirname(os.path.realpath(__file__)) + '/data'

    if not os.path.exists(data_path):
        os.mkdir(data_path)

    if args.mask is not None:
        filename = data_path + "/{:s}-ids.txt".format(args.mask)
    else:
        filename = data_path + "/full-db-ids.txt"

    with open(filename, 'w') as fids:
        fids.write("\n".join(authors_ids))