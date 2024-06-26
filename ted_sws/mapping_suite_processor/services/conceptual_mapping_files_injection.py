import pathlib
import shutil

import pandas as pd

from ted_sws.mapping_suite_processor import CONCEPTUAL_MAPPINGS_RESOURCES_SHEET_NAME, \
    CONCEPTUAL_MAPPINGS_RML_MODULES_SHEET_NAME, CONCEPTUAL_MAPPINGS_RULES_SHEET_NAME
from ted_sws.mapping_suite_processor.adapters.mapping_suite_reader import FILE_NAME_KEY, REF_INTEGRATION_TESTS_KEY


def mapping_suite_processor_inject_resources(conceptual_mappings_file_path: pathlib.Path,
                                             resources_folder_path: pathlib.Path,
                                             output_resources_folder_path: pathlib.Path
                                             ):
    """
        This function reads the resource names from conceptual_mappings_file_path,
         and then, based on the list of resource names,
          the resources in resources_folder_path will be copied to output_resource_folder_path.
    :param conceptual_mappings_file_path:
    :param resources_folder_path:
    :param output_resources_folder_path:
    :return:
    """
    resources_df = pd.read_excel(conceptual_mappings_file_path,
                                 sheet_name=CONCEPTUAL_MAPPINGS_RESOURCES_SHEET_NAME)
    resource_file_names = list(resources_df[FILE_NAME_KEY].values)
    for resource_file_name in resource_file_names:
        src_resource_file_path = resources_folder_path / resource_file_name
        dest_resource_file_path = output_resources_folder_path / resource_file_name
        shutil.copy(src_resource_file_path, dest_resource_file_path)


def mapping_suite_processor_inject_rml_modules(conceptual_mappings_file_path: pathlib.Path,
                                               rml_modules_folder_path: pathlib.Path,
                                               output_rml_modules_folder_path: pathlib.Path
                                               ):
    """
        This function reads the RML Modules from conceptual_mappings_file_path, and then, based on this list,
          the resources in rml_modules_folder_path will be copied to output_rml_modules_folder_path.
    :param conceptual_mappings_file_path:
    :param rml_modules_folder_path:
    :param output_rml_modules_folder_path:
    :return:
    """
    rml_modules_df = pd.read_excel(conceptual_mappings_file_path, sheet_name=CONCEPTUAL_MAPPINGS_RML_MODULES_SHEET_NAME)
    rml_module_file_names = list(rml_modules_df[FILE_NAME_KEY].values)
    for rml_module_file_name in rml_module_file_names:
        src_rml_module_file_path = rml_modules_folder_path / rml_module_file_name
        dest_rml_module_file_path = output_rml_modules_folder_path / rml_module_file_name
        shutil.copy(src_rml_module_file_path, dest_rml_module_file_path)


def mapping_suite_processor_inject_shacl_shape(shacl_shape_file_path: pathlib.Path,
                                               output_shacl_shape_folder_path: pathlib.Path):
    """
        This function copies a shacl_shape file to the desired directory.
    :param shacl_shape_file_path:
    :param output_shacl_shape_folder_path:
    :return:
    """
    dest_shacl_shape_file_path = output_shacl_shape_folder_path / shacl_shape_file_path.name
    shutil.copy(shacl_shape_file_path, dest_shacl_shape_file_path)


def mapping_suite_processor_inject_shacl_shapes(shacl_shape_folder_path: pathlib.Path,
                                                output_shacl_shape_folder_path: pathlib.Path):
    """
        This function copies shacl_shape files folder to the desired directory.
    :param shacl_shape_folder_path:
    :param output_shacl_shape_folder_path:
    :return:
    """
    shutil.copytree(shacl_shape_folder_path, output_shacl_shape_folder_path, dirs_exist_ok=True)


def mapping_suite_processor_inject_sparql_queries(sparql_queries_folder_path: pathlib.Path,
                                                  output_sparql_queries_folder_path: pathlib.Path
                                                  ):
    """
       This function copies SPARQL queries from the source folder to the destination folder.
    :param sparql_queries_folder_path:
    :param output_sparql_queries_folder_path:
    :return:
    """
    shutil.copytree(sparql_queries_folder_path, output_sparql_queries_folder_path, dirs_exist_ok=True)


def mapping_suite_processor_inject_integration_sparql_queries(
        conceptual_mappings_file_path: pathlib.Path,
        sparql_queries_folder_path: pathlib.Path,
        output_sparql_queries_folder_path: pathlib.Path
):
    """
        This function reads the SPARQL files from conceptual_mappings_file_path Rules sheet, and then,
        based on this list,
        the resources in sparql_queries_folder_path will be copied to output_sparql_queries_folder_path.
        :param conceptual_mappings_file_path:
        :param sparql_queries_folder_path:
        :param output_sparql_queries_folder_path:
        :return:
        """
    sparql_files_df = pd.read_excel(conceptual_mappings_file_path, sheet_name=CONCEPTUAL_MAPPINGS_RULES_SHEET_NAME,
                                    skiprows=1)
    sparql_df_values = sparql_files_df[REF_INTEGRATION_TESTS_KEY].dropna().str.split(',').values.tolist()
    sparql_files_names = list(set([item.strip() for sublist in sparql_df_values for item in sublist]))
    for sparql_file_name in sparql_files_names:
        src_sparql_file_path = sparql_queries_folder_path / sparql_file_name
        dest_sparql_file_path = output_sparql_queries_folder_path / sparql_file_name
        if src_sparql_file_path.exists():
            shutil.copy(src_sparql_file_path, dest_sparql_file_path)

