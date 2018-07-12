import rdflib
from xml.sax import SAXParseException

class RDFHandler(object):
    def __init__(self):
        pass
    
    def parse_string(self, string):
        graph = rdflib.Graph()
        
        try:
            graph.parse(data=string)
            return graph
        except SAXParseException:
            return None
        