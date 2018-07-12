# Copyright (c) 2009-2014 Simon Kennedy <sffjunkie+code@gmail.com>

import rdflib
import logging
import datetime
import xml.etree.ElementTree as ET

from mogul.media import MediaHandler

NSMAP = [
    ('aux',           'http://ns.adobe.com/exif/1.0/aux/'),
    ('crs',           'http://ns.adobe.com/camera-raw-settings/1.0/'),
    ('dc',            'http://purl.org/dc/elements/1.1/'),
    ('exif',          'http://ns.adobe.com/exif/1.0/'),
    ('Geotate',       'http://www.geotate.com/Geotate/1.0/'),
    ('Iptc4xmpCore',  'http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/'),
    ('Iptc4xmpExt',   'http://iptc.org/std/Iptc4xmpExt/2008-02-29/'),
    ('lr',            'http://ns.adobe.com/lightroom/1.0/'),
    ('monashkashgar', 'http://monash.edu.au/merc/kashgar/2011/monashkashgar'),
    ('pdf',           'http://ns.adobe.com/pdf/1.3/'),
    ('photomechanic', 'http://ns.camerabits.com/photomechanic/1.0/'),
    ('photoshop',     'http://ns.adobe.com/photoshop/1.0/'),
    ('plus',          'http://ns.useplus.org/ldf/xmp/1.0/'),
    ('rdf',           'http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
    ('tiff',          'http://ns.adobe.com/tiff/1.0/'),
    ('x',             'adobe:ns:meta/'),
    ('xmpBJ',         'http://ns.adobe.com/xap/1.0/bj/'),
    ('xmpDM',         'http://ns.adobe.com/xap/1.0/DynamicMedia/'),
    ('xapMM',         'http://ns.adobe.com/xap/1.0/mm/'),
    ('xmpTPg',        'http://ns.adobe.com/xap/1.0/t/pg/'),
    ('stDim',         'http://ns.adobe.com/xap/1.0/sType/Dimensions#'),
    ('stEvt',         'http://ns.adobe.com/xap/1.0/sType/ResourceEvent#'),
    ('stRef',         'http://ns.adobe.com/xap/1.0/sType/ResourceRef#'),
    ('stFnt',         'http:ns.adobe.com/xap/1.0/sType/Font#'),
    ('stJob',         'http://ns.adobe.com/xap/1.0/sType/Job#'),
    ('stVer',         'http://ns.adobe.com/xap/1.0/sType/Version#'),
    ('xapGImg',       'http://ns.adobe.com/xap/1.0/g/img/'),
    ('xapRights',     'http://ns.adobe.com/xap/1.0/rights/'),
    ('xmp',           'http://ns.adobe.com/xap/1.0/'),
]

class Alt(object):
    def __init__(self):
        self.alternates = []
        
    def __str__(self):
        return self.default()
        
    def __getitem__(self, key):
        for alt in self.alternates:
            if alt[1] == key:
                return alt[0]
            
        return self.default()
    
    def append(self, value):
        if isinstance(value, tuple):
            self.alternates.append(value)
        else:
            self.alternates.append((value, 'x-default'))
        
    def default(self):
        for alt in self.alternates:
            if alt[1] == 'x-default':
                return alt[0]
            
        return self.alternates[0]


class XMPHandler(MediaHandler):
    def __init__(self, log_indent_level=0):
        super(XMPHandler, self).__init__(log_indent_level)
        
        self.metadata = {}
        
        self._packet_id = ''
        self.logger = logging.getLogger('mogul.media')
    
    def read_stream(self, ds, length=-1):
        data = ds.read(length)
        
        namespaces = {}
        for ns, uri in NSMAP:
            namespaces[ns] = uri
        
        doc = ET.fromstring(data)
        rdf = doc.find('rdf:RDF', namespaces=namespaces)
        if rdf is None:
            raise Exception('No XMP metadata found')
        
        rdf_data = ET.tostring(rdf)
        
        self._graph = rdflib.Graph()
        
        for ns, uri in NSMAP:
            self._graph.bind(ns, uri)

        self._graph.parse(data=rdf_data)
        self._extract_metadata_from_graph()
        self._process_metadata()

    def _extract_metadata_from_graph(self):        
        root_subject = rdflib.term.URIRef('')
        for _s,p,o in self._graph.triples([root_subject,None,None]):
            for ns, uri in NSMAP:
                if p.startswith(uri):
                    key = p[len(uri):]
                    if ns not in self.metadata:
                        self.metadata[ns] = {}
                
                    #self.logger.debug('%s : %s : %s' % (_s, p, o))
                    
                    if isinstance(o, rdflib.term.BNode):
                        value = self._handle_bnode(o)
                        self.metadata[ns][key] = value
                    else:
                        self.metadata[ns][key] = str(o)
                        
                    break
            else:
                self.logger.error('XMP: Unknown namespace URI %s' % p)

    def _process_metadata(self):
        self._handle_iso8601_datetime('dc', 'date')
        self._handle_iso8601_datetime('exif', 'DateTimeOriginal')
        self._handle_iso8601_datetime('exif', 'DateTimeDigitized')
        self._handle_iso8601_datetime('photoshop', 'DateCreated')
        self._handle_iso8601_datetime('tiif', 'DateTime')
        self._handle_iso8601_datetime('xmp', 'CreateDate')
        self._handle_iso8601_datetime('xmp', 'MetadataDate')
        self._handle_iso8601_datetime('xmp', 'ModifyDate')

    def _handle_bnode(self, o):
        types = list(self._graph.triples([o,rdflib.RDF.type,None]))
        if len(types) > 1:
            raise ValueError('Multiple types found in object')
        elif len(types) == 1:
            t = types[0][2]
            if t == rdflib.RDF.Seq:
                data = self._handle_list(o)
            elif t == rdflib.RDF.Bag:
                data = self._handle_list(o)
            elif t == rdflib.RDF.Alt:
                data = self._handle_alt(o)
            else:
                raise ValueError("Don't know how to handle %s" % t)
        else:
            data = self._handle_other(o)
            
        return data

    def _handle_list(self, o):
        data = []
        for _s1, p1, o1 in self._graph.triples([o, None, None]):
            if p1 != rdflib.RDF.type:
                if isinstance(o1, rdflib.term.BNode):
                    value = self._handle_bnode(o1)
                else:
                    value = str(o1)
                    
                _uri, fragment = str(p1).split('#')
                if fragment[0] != '_':
                    raise ValueError('Unable to parse index %s', fragment)
                else:
                    index = int(fragment[1])
                    if index > len(data):
                        data.extend([None] * (index - len(data)))
                    data[index - 1] = value
        
        return data

    def _handle_alt(self, o):
        data = Alt()
        for _s1, p1, o1 in self._graph.triples([o, None, None]):
            if p1 != rdflib.RDF.type:
                if isinstance(o1, rdflib.term.BNode):
                    data = self._handle_bnode(o1)
                else:
                    data.alternates.append((str(o1), o1.language))
        
        return data
    
    def _handle_other(self, o):
        data = {}
        for _s1, p1, o1 in self._graph.triples([o, None, None]):
            for ns, uri in NSMAP:
                if p1.startswith(uri):
                    if ns not in data:
                        data[ns] = {}
                    
                    key = p1[len(uri):]
                    data[ns][key] = str(o1)
                    break 

        return data
    
    def _handle_iso8601_datetime(self, ns, key):
        try:
            dt = self.metadata[ns][key]
        except KeyError:
            return

        formats = ['%Y', '%Y-%m', '%Y-%m-%d',
                   '%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%MZ', '%Y-%m-%dT%H:%M%z',
                   '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S%z',
                   '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S.%f%z']
        
        for f in formats:
            try:
                self.metadata[ns][key] = datetime.datetime.strptime(dt, f)
                break
            except:
                pass

    