from mogul.media.rdf import RDFHandler
from mogul.media.xmp import NSMAP

def test_RDF_EmptyString_ParsesOK():
    rdf=''
    
    handler = RDFHandler()
    doc = handler.parse_string(rdf)
    
    assert doc is None

def test_RDF_EmptyDocument_ParsesOK():
    rdf = """
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    </rdf:RDF>
    """
    
    handler = RDFHandler()
    doc = handler.parse_string(rdf)
    
    assert doc is not None

def test_xapMM_ResourceSeq():
    rdf = """
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <rdf:Description rdf:about=""
              xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/">
           <xmpMM:InstanceID>xmp.iid:1ACAE61AE703DF1198A78BAE0A5545DF</xmpMM:InstanceID>
        </rdf:Description>
    </rdf:RDF>
    """
    
    handler = RDFHandler()
    doc = handler.parse_string(rdf)
    
    assert doc['xmpMM']['InstanceID'] == 'xmp.iid:1ACAE61AE703DF1198A78BAE0A5545DF'

if __name__ == '__main__':
    test_RDF_EmptyString_ParsesOK()
    test_RDF_EmptyDocument_ParsesOK()
    test_xapMM_ResourceSeq()
    