"""Validate and query the book's small candidate dataset.

This checks reviewed RDF candidates; it does not run an LLM or Semantica.
"""
import json
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF
from pyshacl import validate

EX = Namespace('https://example.org/enterprise/')
DATA = '''
@prefix ex: <https://example.org/enterprise/> .
ex:C-001 a ex:Customer .
ex:O-001 a ex:Order ; ex:belongsTo ex:C-001 .
'''
SHAPES = '''
@prefix ex: <https://example.org/enterprise/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
ex:OrderShape a sh:NodeShape ; sh:targetClass ex:Order ;
  sh:property [ sh:path ex:belongsTo ; sh:minCount 1 ;
                sh:maxCount 1 ; sh:class ex:Customer ] .
'''
QUERY = '''
PREFIX ex: <https://example.org/enterprise/>
SELECT ?customer WHERE { ex:O-001 ex:belongsTo ?customer }
'''

def run():
    data = Graph().parse(data=DATA, format='turtle')
    shapes = Graph().parse(data=SHAPES, format='turtle')
    passed, _, _ = validate(data, shacl_graph=shapes, inference='none')
    assert passed, 'Reviewed input must pass'
    rows = [str(row.customer) for row in data.query(QUERY)]
    assert rows == [str(EX['C-001'])], rows
    data.remove((EX['O-001'], EX.belongsTo, None))
    missing, _, _ = validate(data, shacl_graph=shapes, inference='none')
    assert not missing, 'A missing customer link must fail'
    data.add((EX['O-001'], EX.belongsTo, URIRef(str(EX['E-001']))))
    data.add((EX['E-001'], RDF.type, EX.Equipment))
    wrong_type, _, _ = validate(data, shacl_graph=shapes, inference='none')
    assert not wrong_type, 'An Equipment endpoint instead of a Customer must fail'
    print(json.dumps({'valid_candidate': passed, 'customers': rows,
                      'missing_link_rejected': not missing,
                      'wrong_type_rejected': not wrong_type}, indent=2))

if __name__ == '__main__':
    run()
