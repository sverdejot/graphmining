import re, gzip
from lxml import etree
from tqdm import tqdm
import argparse

class Decoder:    
    '''
    Decodificador para el archivo XMl que transcribe de ISO-8859-1 a UTF-8 con las transcripciones especificadas en el archivo DTD

    Parameters
    ----------
        xml_path : str
            directorio del archivo fuente XML (comprimido)
        
        decoded_xml_path : str
            directorio donde se almacena el XML decodificado (comprimido)

        dtd_path : str
            directorio del fichero de definicion de tipos

    Attributes
    ----------
        src : str
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
    entity_re = re.compile(r'&(\w+);')
    
    def __init__(self, xml_path, decoded_xml_path, dtd_path):
        self.src = xml_path
        self.dst = decoded_xml_path
        self.dtd = etree.DTD(dtd_path)
        self.replacements = {x.name: x.content for x in self.dtd.entities()}

    def resolve_entity(self, m):
        '''
        Sustituye la cadena pasada por su transcripcion en el DTD. Por ejemplo, para la cadena "&Ouml;" la reemplazará por "&#214;".

        Las cadenas de la forma "&€[0-9]+;" no van a ser reemplazadas.
        Si alguna de las transcripciones del archivo DTD contiene la cadena "<", el metodo no comprobara si esto hace que el XML este mal formado.

        Parameters
        ----------
            m : string
                palabra para comprobar su transcripcion en el DTD

        Returns
        -------
            replace : String
                cadena con transcripcion correspondiente o, si no se ha encontraWdo, cadena original
        
        '''
        return self.replacements.get(m.group(1),f'&{m.group(1)};')

    def expand_line(self, line):
        ''' 
        Comprueba la transcripcion de una linea palabra por palabra

        Parameters
        ----------
            line : str
                linea para obtener su transcripcion
        
        Returns
        -------
            line : str
                linea transcrita o, si no tiene, original
        '''
        return self.entity_re.sub(self.resolve_entity,line)

    def recode_file(self):
        '''
        Decodifica el archivo linea por linea

        Parameters
        ----------
            src : str

            dst : str

        Returns
        -------
            dst : str
                directorio donde esta almacenada la base de datos decodificada
        '''
        with gzip.open(self.src,mode='rt', encoding='ISO-8859-1', newline='\n') as src_file:
            #with gzip.open(self.dst, mode='wt', encoding='UTF-8', newline='\n') as dst_file:
            with open(self.dst, mode='wt', encoding='UTF-8', newline='\n') as dst_file:
                ''' Reemplaza la codificacion por la correcta (primera linea del xml) '''
                src_file.readline()
                dst_file.write('<?xml version="1.0" encoding="UTF-8"?>\n') 
                for line in tqdm(src_file, desc='Decodificando fichero XML'):
                    dst_file.write(self.expand_line(line))

        return self.dst

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()

    # Obtención de los argumentos
    arg_parser.add_argument("xml_path", help="Directorio del fichero comprimido de dblp", type=str)
    arg_parser.add_argument("decoded_xml_path", help="Directorio donde se guardará el fichero decodificado (comprimido)", type=str)
    arg_parser.add_argument("dtd_path", help="Directorio del fichero de transcripciones", type=str)

    args = arg_parser.parse_args()

    dc = Decoder(xml_path=args.xml_path, decoded_xml_path=args.decoded_xml_path, dtd_path=args.dtd_path)
    dc.recode_file()