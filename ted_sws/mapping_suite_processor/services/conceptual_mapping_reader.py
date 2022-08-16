import pathlib
from typing import Dict, Union

import numpy as np
import pandas as pd

from ted_sws.core.model.transform import ConceptualMapping, ConceptualMappingXPATH, ConceptualMappingMetadata
from ted_sws.mapping_suite_processor import CONCEPTUAL_MAPPINGS_METADATA_SHEET_NAME, \
    CONCEPTUAL_MAPPINGS_RULES_SHEET_NAME, RULES_FIELD_XPATH, RULES_E_FORM_BT_NAME, RULES_SF_FIELD_ID, RULES_E_FORM_BT_ID
from ted_sws.notice_validator import BASE_XPATH_FIELD

CONCEPTUAL_MAPPINGS_FILE_NAME = "conceptual_mappings.xlsx"


def mapping_suite_read_metadata(conceptual_mappings_file_path: pathlib.Path) -> Dict:
    """
        This feature allows you to read the conceptual mapping metadata.
    :param conceptual_mappings_file_path:
    :return:
    """

    with open(conceptual_mappings_file_path, 'rb') as excel_file:
        metadata_df = pd.read_excel(excel_file, sheet_name=CONCEPTUAL_MAPPINGS_METADATA_SHEET_NAME)
        metadata = metadata_df.set_index('Field').T.to_dict('list')

    return metadata


def mapping_suite_read_conceptual_mapping(conceptual_mappings_file_path: pathlib.Path) -> \
        Union[ConceptualMapping, None]:
    """
        This feature allows you to read the c1onceptual mapping in a package.
    :param conceptual_mappings_file_path:
    :param metadata:
    :return:
    """

    if not conceptual_mappings_file_path.exists():
        return None

    metadata = mapping_suite_read_metadata(conceptual_mappings_file_path)
    conceptual_mapping = ConceptualMapping()
    conceptual_mapping_xpaths = []
    with open(conceptual_mappings_file_path, 'rb') as excel_file:
        base_xpath = metadata[BASE_XPATH_FIELD][0]
        rules_df = pd.read_excel(excel_file, sheet_name=CONCEPTUAL_MAPPINGS_RULES_SHEET_NAME, header=1)
        df_xpaths = rules_df[RULES_FIELD_XPATH].tolist()
        df_bt_names = rules_df[RULES_E_FORM_BT_NAME].tolist()
        df_eform_bt_ids = rules_df[RULES_E_FORM_BT_ID].tolist()
        df_sform_field_ids = rules_df[RULES_SF_FIELD_ID].tolist()
        processed_xpaths = set()
        for idx, xpath_row in enumerate(df_xpaths):
            if xpath_row is not np.nan:
                row_xpaths = xpath_row.split('\n')
                for xpath in row_xpaths:
                    if xpath:
                        xpath = base_xpath + "/" + xpath
                        if xpath not in processed_xpaths:
                            xpath_name = df_bt_names[idx] if df_bt_names[idx] is not np.nan else None
                            eform_bt_id = df_eform_bt_ids[idx] if df_eform_bt_ids[idx] is not np.nan else None
                            sform_field_id = df_sform_field_ids[idx] if df_sform_field_ids[idx] is not np.nan else None

                            cm_xpath: ConceptualMappingXPATH = ConceptualMappingXPATH(
                                xpath=xpath,
                                name=xpath_name,
                                standard_form_field_id=sform_field_id,
                                eform_bt_id=eform_bt_id
                            )
                            conceptual_mapping_xpaths.append(cm_xpath)
                            processed_xpaths.add(xpath)

    conceptual_mapping.xpaths = conceptual_mapping_xpaths
    cm_metadata = ConceptualMappingMetadata()
    cm_metadata.base_xpath = base_xpath
    conceptual_mapping.metadata = cm_metadata

    return conceptual_mapping