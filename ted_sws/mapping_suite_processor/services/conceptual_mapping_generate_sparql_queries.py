import pathlib
import re
from typing import Iterator

import pandas as pd

from ted_sws.mapping_suite_processor import CONCEPTUAL_MAPPINGS_METADATA_SHEET_NAME, \
    CONCEPTUAL_MAPPINGS_RULES_SHEET_NAME, RULES_FIELD_XPATH, RULES_E_FORM_BT_NAME, RULES_SF_FIELD_ID, RULES_E_FORM_BT_ID
from ted_sws.notice_validator import BASE_XPATH_FIELD
from ted_sws.resources.prefixes import PREFIXES_DEFINITIONS

RULES_SF_FIELD_NAME = 'Standard Form Field Name (M)'
RULES_CLASS_PATH = 'Class path (M)'
RULES_PROPERTY_PATH = 'Property path (M)'

CL_FIELD_VALUE = 'Field Value (in XML)'
CL_MAPPING_REFERENCE = 'Mapping Reference (in ePO)'

DEFAULT_RQ_NAME = 'sparql_query_'

SPARQL_PREFIX_PATTERN = re.compile('(?:\\s+|^)(\\w+)?:')
SPARQL_PREFIX_LINE = 'PREFIX {prefix}: <{value}>'


def get_sparql_prefixes(sparql_q: str) -> set:
    finds: list = re.findall(SPARQL_PREFIX_PATTERN, sparql_q)
    return set(finds)


def concat_field_xpath(base_xpath: str, field_xpath: str, separator: str = ", ") -> str:
    base_xpath = base_xpath if not pd.isna(base_xpath) else ''
    field_xpath = field_xpath if not pd.isna(field_xpath) else ''
    base_xpath = (base_xpath + "/") if field_xpath else base_xpath
    return separator.join([base_xpath + xpath for xpath in field_xpath.splitlines()])


def get_elem_reference(class_value: str, cl_dfs: dict, field_xpath: str) -> str:

    if '(from ' in class_value:
        class_name = class_value.split()[0].split(':')[-1].lower()
        cl_id = class_value.split()[-1][:-1]
        cl_sheet = pd.DataFrame()
        for sheet_name in cl_dfs:
            if sheet_name.startswith(cl_id):
                cl_sheet = cl_dfs[sheet_name]
        for index, row in cl_sheet.iterrows():
            tmp_row = row[CL_FIELD_VALUE]
            if class_name == tmp_row.split()[0] and field_xpath == tmp_row.split()[-1]:
                return row[CL_MAPPING_REFERENCE]
    else:
        return class_value.split()[0]

    return ''


def generate_subject_type(class_path: str, cl_dfs: dict, field_xpath: str) -> str:
    subject_reference = get_elem_reference(class_path.split(' / ')[0], cl_dfs,
                                           field_xpath.split('/')[0].lower() if not pd.isna(field_xpath) else '')
    return f"?this rdf:type {subject_reference} ." if subject_reference else ''


def generate_object_type(class_path: str, cl_dfs: dict, field_xpath: str) -> str:
    object_reference = get_elem_reference(class_path.split(' / ')[-1], cl_dfs,
                                          field_xpath.split('/')[-1].lower() if not pd.isna(field_xpath) else '')
    return f"?value rdf:type {object_reference} ." if object_reference else ''


def sparql_validation_generator(data: pd.DataFrame, base_xpath: str, cl_dfs: dict) -> Iterator[str]:
    """
        This function generates SPARQL queries based on data in the dataframe.
    :param data:
    :param base_xpath:
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
        prefixes = [SPARQL_PREFIX_LINE.format(
            prefix=prefix, value=PREFIXES_DEFINITIONS.get(prefix)
        ) for prefix in get_sparql_prefixes(property_path)]
        yield f"#title: {sf_field_id} - {sf_field_name}\n" \
              f"#description: “{sf_field_id} - {sf_field_name}” in SF corresponds to “{e_form_bt_id} " \
              f"{e_form_bt_name}” in eForms. The corresponding XML element is " \
              f"{concat_field_xpath(base_xpath, field_xpath)}. " \
              f"The expected ontology instances are epo: {class_path} .\n" \
              f"#xpath: {concat_field_xpath(base_xpath, field_xpath, separator=',')}" \
              "\n" + "\n" + "\n".join(prefixes) + "\n\n" \
                                                  f"ASK WHERE {{ \n\t\t" \
                                                  f"{generate_subject_type(class_path, cl_dfs, field_xpath)}\n\t\t" \
                                                  f"{generate_object_type(class_path, cl_dfs, field_xpath)}\n\t\t" \
                                                  f"{property_path} }}"


def mapping_suite_processor_generate_sparql_queries(conceptual_mappings_file_path: pathlib.Path,
                                                    output_sparql_queries_folder_path: pathlib.Path,
                                                    rq_name: str = DEFAULT_RQ_NAME):
    """
    This function reads data from conceptual_mappings.xlsx and generates SPARQL validation queries in provided
    package. :param conceptual_mappings_file_path: :param output_sparql_queries_folder_path: :param rq_name: :return:
    """
    with open(conceptual_mappings_file_path, 'rb') as excel_file:
        conceptual_mappings_df = pd.read_excel(excel_file, sheet_name=None)

        cl_dfs = {}
        for SHEET_NAMES in conceptual_mappings_df:
            if SHEET_NAMES.startswith('CL'):
                conceptual_mappings_df[SHEET_NAMES].columns = conceptual_mappings_df[SHEET_NAMES].iloc[0]
                conceptual_mappings_df[SHEET_NAMES] = conceptual_mappings_df[SHEET_NAMES][1:]
                cl_dfs[SHEET_NAMES] = conceptual_mappings_df[SHEET_NAMES][
                    conceptual_mappings_df[SHEET_NAMES][[CL_FIELD_VALUE, CL_MAPPING_REFERENCE]].notnull()]

        conceptual_mappings_rules_df = conceptual_mappings_df[CONCEPTUAL_MAPPINGS_RULES_SHEET_NAME]
        conceptual_mappings_rules_df.columns = conceptual_mappings_rules_df.iloc[0]
        conceptual_mappings_rules_df = conceptual_mappings_rules_df[1:]
        conceptual_mappings_rules_df = conceptual_mappings_rules_df[
            conceptual_mappings_rules_df[RULES_PROPERTY_PATH].notnull()]
        metadata_df = conceptual_mappings_df[CONCEPTUAL_MAPPINGS_METADATA_SHEET_NAME] #pd.read_excel(excel_file, sheet_name=CONCEPTUAL_MAPPINGS_METADATA_SHEET_NAME)
        metadata = metadata_df.set_index('Field').T.to_dict('list')
        base_xpath = metadata[BASE_XPATH_FIELD][0]

    sparql_queries = sparql_validation_generator(conceptual_mappings_rules_df, base_xpath, cl_dfs)

    output_sparql_queries_folder_path.mkdir(parents=True, exist_ok=True)
    for index, sparql_query in enumerate(sparql_queries):
        output_file_path = output_sparql_queries_folder_path / f"{rq_name}{index}.rq"
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.write(sparql_query)
