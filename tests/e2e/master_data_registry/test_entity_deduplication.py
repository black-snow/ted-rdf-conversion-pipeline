import rdflib
from rdflib import OWL

from ted_sws.data_manager.adapters.triple_store import FusekiAdapter
from ted_sws.master_data_registry.services.entity_deduplication import deduplicate_entities_by_cet_uri

TEST_MDR_REPOSITORY = "tmp_mdr_test_repository"
TEST_QUERY_UNIQUE_NAMES = """SELECT distinct ?name
WHERE { ?s a <http://www.w3.org/ns/org#Organization> .
?s <http://www.meaningfy.ws/mdr#isCanonicalEntity> True .
?s <http://data.europa.eu/a4g/ontology#hasLegalName> ?name .
}"""
TEST_QUERY_UNIQUE_CET_ROOTS = """
SELECT distinct ?s
WHERE { ?s a <http://www.w3.org/ns/org#Organization> .
?s <http://www.meaningfy.ws/mdr#isCanonicalEntity> True .
}
"""


def test_deduplicate_entities_by_cet_uri(notice_with_rdf_manifestation, organisation_cet_uri):
    fuseki_triple_store = FusekiAdapter()
    if TEST_MDR_REPOSITORY in fuseki_triple_store.list_repositories():
        fuseki_triple_store.delete_repository(repository_name=TEST_MDR_REPOSITORY)
    fuseki_triple_store.create_repository(repository_name=TEST_MDR_REPOSITORY)
    notice_with_rdf_manifestation.set_distilled_rdf_manifestation(
        distilled_rdf_manifestation=notice_with_rdf_manifestation.rdf_manifestation.copy())
    deduplicate_entities_by_cet_uri(notices=[notice_with_rdf_manifestation], cet_uri=organisation_cet_uri,
                                    mdr_dataset_name=TEST_MDR_REPOSITORY)

    sparql_endpoint = fuseki_triple_store.get_sparql_triple_store_endpoint(repository_name=TEST_MDR_REPOSITORY)
    unique_names = sparql_endpoint.with_query(sparql_query=TEST_QUERY_UNIQUE_NAMES).fetch_tabular()
    unique_cet_roots = sparql_endpoint.with_query(sparql_query=TEST_QUERY_UNIQUE_CET_ROOTS).fetch_tabular()
    assert len(unique_names) == len(unique_cet_roots)

    notice_rdf_content = notice_with_rdf_manifestation.distilled_rdf_manifestation.object_data
    notice_rdf_graph = rdflib.Graph()
    notice_rdf_graph.parse(data=notice_rdf_content, format="ttl")

    non_canonical_same_as_triples = [triple for triple in notice_rdf_graph.triples(triple=(None, OWL.sameAs, None))]
    canonical_cets_set = set(unique_cet_roots["s"].tolist())
    for triple in non_canonical_same_as_triples:
        assert str(triple[2]) in canonical_cets_set

    canonical_cets_same_as_triples = []
    for canonical_cet in canonical_cets_set:
        for triple in notice_rdf_graph.triples(triple=(rdflib.URIRef(canonical_cet), OWL.sameAs, None)):
            canonical_cets_same_as_triples.append(triple)

    for triple in canonical_cets_same_as_triples:
        assert str(triple[2]) in canonical_cets_set

    fuseki_triple_store.delete_repository(repository_name=TEST_MDR_REPOSITORY)
