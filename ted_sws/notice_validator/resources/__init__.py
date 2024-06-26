import pathlib

NOTICE_VALIDATOR_RESOURCES_PATH = pathlib.Path(__file__).parent.resolve()
SPARQL_QUERY_TEMPLATES_PATH = NOTICE_VALIDATOR_RESOURCES_PATH / "sparql_query_templates"
NOTICE_AVAILABILITY_SPARQL_QUERY_TEMPLATE_PATH = SPARQL_QUERY_TEMPLATES_PATH / "check_notice_availability.rq"
NOTICES_AVAILABILITY_SPARQL_QUERY_TEMPLATE_PATH = SPARQL_QUERY_TEMPLATES_PATH / "check_notices_availability.rq"
GET_NOTICE_URI_SPARQL_QUERY_TEMPLATE_PATH = SPARQL_QUERY_TEMPLATES_PATH / "get_notice_uri.rq"
