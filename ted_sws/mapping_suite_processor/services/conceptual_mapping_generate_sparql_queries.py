import pathlib
import re
from typing import Iterator

import pandas as pd

from ted_sws.event_manager.services.log import log_cli_brief_error
from ted_sws.mapping_suite_processor import CONCEPTUAL_MAPPINGS_METADATA_SHEET_NAME, \
    CONCEPTUAL_MAPPINGS_RULES_SHEET_NAME, RULES_FIELD_XPATH, RULES_E_FORM_BT_NAME, RULES_SF_FIELD_ID, \
    RULES_E_FORM_BT_ID, RULES_SF_FIELD_NAME
from ted_sws.mapping_suite_processor.adapters.conceptual_mapping_reader import ConceptualMappingReader
from ted_sws.notice_validator import BASE_XPATH_FIELD
from ted_sws.resources.prefixes import PREFIXES_DEFINITIONS

RULES_CLASS_PATH = 'Class path (M)'
RULES_PROPERTY_PATH = 'Property path (M)'

CL_FIELD_VALUE = 'Field Value (in XML)'
CL_MAPPING_REFERENCE = 'Mapping Reference (in ePO)'
CL_SUPER_TYPE = 'SuperType'
CL_XPATH_FRAGMENT = 'XML PATH Fragment'

DEFAULT_RQ_NAME = 'sparql_query_'

SPARQL_PREFIX_PATTERN = re.compile('(?:\\s+|^)([\\w\\-]+)?:')
SPARQL_PREFIX_LINE = 'PREFIX {prefix}: <{value}>'
SPARQL_LOGGER_NAME = "SPARQL"


def get_sparql_prefixes(sparql_q: str) -> list:
    finds: list = re.findall(SPARQL_PREFIX_PATTERN, sparql_q)
    return sorted(set(finds))


def concat_field_xpath(base_xpath: str, field_xpath: str, separator: str = ", ") -> str:
    base_xpath = base_xpath if not pd.isna(base_xpath) else ''
    field_xpath = field_xpath if not pd.isna(field_xpath) else ''
    return separator.join(
        [ConceptualMappingReader.xpath_with_base(xpath, base_xpath) for xpath in field_xpath.splitlines()]
    )


def _get_elem_reference(class_value: str, cl_dfs: dict, field_xpath: list) -> str:
    if '(from ' in class_value:

        # Find CL sheet
        cl_id = class_value.split()[-1][:-1]
        cl_sheet: pd.DataFrame() = pd.DataFrame()
        for sheet_name in cl_dfs:
            if sheet_name.startswith(cl_id):
                cl_sheet = cl_dfs[sheet_name]

        # Find elem type
        if not cl_sheet.empty:
            class_value = class_value.split()[0]
            for index, row in cl_sheet.iterrows():
                class_super_type = row[CL_SUPER_TYPE]
                xpath_fragment = row[CL_XPATH_FRAGMENT]
                for field_xpath_fragment in reversed(field_xpath):
                    if class_value == class_super_type and field_xpath_fragment == xpath_fragment:
                        return row[CL_MAPPING_REFERENCE]
    else:
        return class_value

    return ''


def _generate_subject_type(class_path: str, cl_dfs: dict, field_xpath: str) -> str:
    subject_reference = _get_elem_reference(class_path.split(' / ')[0], cl_dfs,
                                            field_xpath.split('/') if not pd.isna(field_xpath) else '')
    return f"?this rdf:type {subject_reference} ." if subject_reference else ''


# Could be used later
# def _generate_object_type(class_path: str, cl_dfs: dict, field_xpath: str) -> str:
#     """
#     This method determines SPARQL query object type base on some rules
#     :param class_path:
#     :param cl_dfs:
#     :param field_xpath:
#     :return:
#     """
#     # Temporary solution (could be used in the future)
#     class_path = class_path.split(' / ')[-1]
#     if 'at-voc:' in class_path:
#         return ''
#
#     object_reference = _get_elem_reference(class_path, cl_dfs,
#                                            field_xpath.split('/') if not pd.isna(field_xpath) else '')
#     return f"?value rdf:type {object_reference} ." if object_reference else ''


def sparql_validation_generator(data: pd.DataFrame, base_xpath: str, controlled_list_dfs: dict,
                                prefixes_definitions: dict) -> Iterator[str]:
    """
        This function generates SPARQL queries based on data in the dataframe.
    :param prefixes_definitions:
    :param data:
    :param base_xpath:
    :param controlled_list_dfs:
    :return:
    """

    for index, row in data.iterrows():
        sf_field_id = row[RULES_SF_FIELD_ID]
        sf_field_name = row[RULES_SF_FIELD_NAME]
        e_form_bt_id = row[RULES_E_FORM_BT_ID]
        e_form_bt_name = row[RULES_E_FORM_BT_NAME]
        field_xpath = row[RULES_FIELD_XPATH]
        class_path = row[RULES_CLASS_PATH]
        property_path = row[RULES_PROPERTY_PATH]

        subject_type = _generate_subject_type(class_path, controlled_list_dfs, field_xpath) \
            if '?this' in property_path else ''

        prefixes_string = property_path
        if subject_type:
            prefixes_string += subject_type

        sparql_title_parts = [sf_field_id, sf_field_name]
        sparql_title = " - ".join([item for item in sparql_title_parts if not pd.isnull(item)])

        prefixes = []
        for prefix in get_sparql_prefixes(prefixes_string):
            if prefix in prefixes_definitions:
                prefix_value = prefixes_definitions.get(prefix)
            else:
                # the prefix value is set to "^" on purpose, to generate a syntactically incorrect SPARQL query
                prefix_value = "^"
                log_cli_brief_error(f"'{sf_field_id}': PREFIX '{prefix}' is not defined.", name=SPARQL_LOGGER_NAME)

            prefixes.append(SPARQL_PREFIX_LINE.format(prefix=prefix, value=prefix_value))

        subject_type_display = ('\n\t\t' + subject_type) if subject_type else ''
        yield f"#title: {sparql_title}\n" \
              f"#description: “{sparql_title}” in SF corresponds to “{e_form_bt_id} " \
              f"{e_form_bt_name}” in eForms. The corresponding XML element is " \
              f"{concat_field_xpath(base_xpath, field_xpath)}. " \
              f"The expected ontology instances are epo: {class_path} .\n" \
              f"#xpath: {concat_field_xpath(base_xpath, field_xpath, separator=',')}" \
              "\n" + "\n" + "\n".join(prefixes) + "\n\n" \
                                                  f"ASK WHERE {{ " \
                                                  f"{subject_type_display}" \
                                                  f"\n\t\t{property_path} }}"


def _process_concept_mapping_sheet(sheet: pd.DataFrame) -> pd.DataFrame:
    sheet.columns = sheet.iloc[0]
    return sheet[1:].copy()


def mapping_suite_processor_generate_sparql_queries(conceptual_mappings_file_path: pathlib.Path,
                                                    output_sparql_queries_folder_path: pathlib.Path,
                                                    rq_name: str = DEFAULT_RQ_NAME,
                                                    prefixes_definitions=None):
    """
        This function reads data from conceptual_mappings.xlsx and generates SPARQL validation queries in provided package.
    :param prefixes_definitions:
    :param conceptual_mappings_file_path:
    :param output_sparql_queries_folder_path:
    :param rq_name:
    :return:
    """
    if prefixes_definitions is None:
        prefixes_definitions = PREFIXES_DEFINITIONS

    with open(conceptual_mappings_file_path, 'rb') as excel_file:
        conceptual_mappings_df = pd.read_excel(excel_file, sheet_name=None)
        controlled_list_dfs = {}
        for sheet_name in conceptual_mappings_df:
            if sheet_name.startswith('CL'):
                controlled_list_dfs[sheet_name] = _process_concept_mapping_sheet(conceptual_mappings_df[sheet_name])
        conceptual_mappings_rules_df = _process_concept_mapping_sheet(
            conceptual_mappings_df[CONCEPTUAL_MAPPINGS_RULES_SHEET_NAME])
        conceptual_mappings_rules_df[RULES_SF_FIELD_ID].ffill(axis="index", inplace=True)
        conceptual_mappings_rules_df[RULES_SF_FIELD_NAME].ffill(axis="index", inplace=True)
        conceptual_mappings_rules_df = conceptual_mappings_rules_df[
            conceptual_mappings_rules_df[RULES_PROPERTY_PATH].notnull()]
        metadata_df = conceptual_mappings_df[CONCEPTUAL_MAPPINGS_METADATA_SHEET_NAME]
        metadata = metadata_df.set_index('Field').T.to_dict('list')
        base_xpath = metadata[BASE_XPATH_FIELD][0]

    sparql_queries = sparql_validation_generator(conceptual_mappings_rules_df, base_xpath, controlled_list_dfs,
                                                 prefixes_definitions)

    output_sparql_queries_folder_path.mkdir(parents=True, exist_ok=True)
    for index, sparql_query in enumerate(sparql_queries):
        output_file_path = output_sparql_queries_folder_path / f"{rq_name}{index}.rq"
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(sparql_query)
