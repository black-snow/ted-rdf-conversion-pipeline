import json
import pathlib
from typing import List, Union

from ted_sws.core.model.transform import MetadataConstraints
from ted_sws.data_manager.adapters.mapping_suite_repository import MS_TRANSFORM_FOLDER_NAME, MS_TEST_DATA_FOLDER_NAME, \
    MS_CONCEPTUAL_MAPPING_FILE_NAME, MS_RESOURCES_FOLDER_NAME, MS_MAPPINGS_FOLDER_NAME, MS_METADATA_FILE_NAME, \
    MS_VALIDATE_FOLDER_NAME, MS_SPARQL_FOLDER_NAME, MS_SHACL_FOLDER_NAME, MS_OUTPUT_FOLDER_NAME, MS_TEST_SUITE_REPORT
from ted_sws.event_manager.model.event_message import EventMessage, EventMessageLogSettings
from ted_sws.event_manager.services.logger_from_context import get_console_logger
from ted_sws.mapping_suite_processor.adapters.mapping_suite_hasher import MappingSuiteHasher
from ted_sws.mapping_suite_processor.services.conceptual_mapping_generate_metadata import VERSION_FIELD, \
    MAPPING_SUITE_HASH, VERSION_KEY
from ted_sws.mapping_suite_processor.services.conceptual_mapping_reader import mapping_suite_read_metadata

SHACL_KEYWORD = "shacl"
SPARQL_KEYWORD = "sparql"
XPATH_KEYWORD = "xpath"

REPORTS_KEYWORDS = [SHACL_KEYWORD, SPARQL_KEYWORD, XPATH_KEYWORD]


class MappingSuiteStructureValidator:
    reports_min_count: int = 3

    def __init__(self, mapping_suite_path: Union[pathlib.Path, str]):
        self.mapping_suite_path = pathlib.Path(mapping_suite_path)
        self.logger = get_console_logger(name="MappingSuiteStructureValidator")
        self.log_settings = EventMessageLogSettings(briefly=True)

    def assert_path(self, assertion_path_list: List[pathlib.Path]) -> bool:
        """
            Validate whether the given path exists and is non-empty.
        """
        success = True
        for path_item in assertion_path_list:
            message_path_not_found = f"Path not found: {path_item}"
            if not path_item.exists():
                self.logger.error(event_message=EventMessage(message=message_path_not_found),
                                  settings=self.log_settings)
                success = False
                continue

            if path_item.is_dir():
                message_folder_empty = f"Folder is empty: {path_item}"
                if not any(path_item.iterdir()):
                    self.logger.error(event_message=EventMessage(message=message_folder_empty),
                                      settings=self.log_settings)
                    success = False
            else:
                message_file_is_empty = f"File is empty: {path_item}"
                if path_item.stat().st_size <= 0:
                    self.logger.error(event_message=EventMessage(message=message_file_is_empty),
                                      settings=self.log_settings)
                    success = False

        return success

    def validate_core_structure(self) -> bool:
        """
            Check whether the core mapping suite structure is in place.
        """
        self.logger.info(
            event_message=EventMessage(
                message="Check whether the core mapping suite structure is in place."),
            settings=self.log_settings)
        mandatory_paths_l1 = [
            self.mapping_suite_path / MS_TRANSFORM_FOLDER_NAME,
            self.mapping_suite_path / MS_TRANSFORM_FOLDER_NAME / MS_MAPPINGS_FOLDER_NAME,
            self.mapping_suite_path / MS_TRANSFORM_FOLDER_NAME / MS_RESOURCES_FOLDER_NAME,
            self.mapping_suite_path / MS_TRANSFORM_FOLDER_NAME / MS_CONCEPTUAL_MAPPING_FILE_NAME,
            self.mapping_suite_path / MS_TEST_DATA_FOLDER_NAME
        ]
        return self.assert_path(mandatory_paths_l1)

    def validate_expanded_structure(self) -> bool:
        """
            Check if the expanded mapping suite structure is in place
        """
        self.logger.info(
            event_message=EventMessage(
                message="Check if the expanded mapping suite structure is in place."),
            settings=self.log_settings)

        mandatory_paths_l2 = [
            self.mapping_suite_path / MS_METADATA_FILE_NAME,
            self.mapping_suite_path / MS_VALIDATE_FOLDER_NAME,
            self.mapping_suite_path / MS_VALIDATE_FOLDER_NAME / MS_SPARQL_FOLDER_NAME,
            self.mapping_suite_path / MS_VALIDATE_FOLDER_NAME / MS_SHACL_FOLDER_NAME,
        ]
        return self.assert_path(mandatory_paths_l2)

    def validate_output_structure(self) -> bool:
        """
            Check if the transformed and validated mapping suite structure is in place.
        """

        self.logger.info(
            event_message=EventMessage(
                message="Check if the transformed and validated mapping suite structure is in place."),
            settings=self.log_settings)

        success = True

        def _iter_dir(path):
            return [i for i in path.iterdir() if i.is_dir()]

        mandatory_paths_l3 = [
            self.mapping_suite_path / MS_OUTPUT_FOLDER_NAME,
        ]

        success = success and self.assert_path(mandatory_paths_l3)
        if success:
            output_path = self.mapping_suite_path / MS_OUTPUT_FOLDER_NAME
            notices_rdf_files_paths = [path for path in output_path.rglob("*.ttl") if path.is_file()]
            for notice_rdf_path in notices_rdf_files_paths:
                notice_path = notice_rdf_path.parent
                report_count = 0
                success = success and self.assert_path([notice_path / MS_TEST_SUITE_REPORT])
                if success:
                    for report in (notice_path / MS_TEST_SUITE_REPORT).iterdir():
                        if any(keyword in report.name for keyword in REPORTS_KEYWORDS):
                            report_count += 1
                    if report_count < self.reports_min_count:
                        self.logger.error(
                            event_message=EventMessage(message=f"{notice_path.stem} has missing validation reports."),
                            settings=self.log_settings)
                        success = False
                        break

        return success

    def check_metadata_consistency(self, package_metadata_path=None) -> bool:

        """
            Read the conceptual mapping XSLX and the metadata.json and compare the contents,
            in particular paying attention to the mapping suite version and the ontology version.
        """
        self.logger.info(
            event_message=EventMessage(
                message="Read the conceptual mapping XSLX and the metadata.json and compare the contents."),
            settings=self.log_settings)
        success = True

        conceptual_mappings_document = mapping_suite_read_metadata(
            conceptual_mappings_file_path=self.mapping_suite_path / MS_TRANSFORM_FOLDER_NAME / MS_CONCEPTUAL_MAPPING_FILE_NAME)
        conceptual_mappings_version = [val for val in conceptual_mappings_document.values()][4][0]
        conceptual_mappings_epo_version = [val for val in conceptual_mappings_document.values()][5][0]

        if package_metadata_path is None:
            package_metadata_path = self.mapping_suite_path / MS_METADATA_FILE_NAME
        package_metadata_content = package_metadata_path.read_text(encoding="utf-8")
        package_metadata = json.loads(package_metadata_content)
        package_metadata['metadata_constraints'] = MetadataConstraints(**package_metadata['metadata_constraints'])
        metadata_version = [val for val in package_metadata.values()][3]
        metadata_epo_version = [val for val in package_metadata.values()][4]

        if not (
                conceptual_mappings_version >= metadata_version
                and conceptual_mappings_epo_version >= metadata_epo_version
        ):
            event_message = EventMessage(
                message=f'Not the same value between metadata.json [version {metadata_version}, epo_version {metadata_epo_version}] and conceptual_mapping_file [version {conceptual_mappings_version}, epo_version {conceptual_mappings_epo_version}]')
            self.logger.error(event_message=event_message, settings=self.log_settings)
            success = False

        return success

    def check_for_changes_by_version(self) -> bool:
        """
            This function check whether the mapping suite is well versioned and no changes detected.

            We want to ensure that:
             - the version in the metadata.json is the same as the version in the conceptual mappings
             - the version in always incremented
             - the changes in the mapping suite are detected by comparison to the hash in the metadata.json
             - the hash is bound to a version of the mapping suite written in the conceptual mappings
             - the version-bound-hash and the version are written in the metadata.json and are the same
             to the version in the conceptual mappings
        """
        self.logger.info(
            event_message=EventMessage(
                message="Check whether the mapping suite is well versioned and no changes detected."),
            settings=self.log_settings)
        success = True

        conceptual_mapping_metadata = mapping_suite_read_metadata(
            conceptual_mappings_file_path=self.mapping_suite_path / MS_TRANSFORM_FOLDER_NAME / MS_CONCEPTUAL_MAPPING_FILE_NAME)

        metadata_json = json.loads((self.mapping_suite_path / MS_METADATA_FILE_NAME).read_text())

        version_in_cm = conceptual_mapping_metadata[VERSION_FIELD][0]
        mapping_suite_versioned_hash = MappingSuiteHasher(self.mapping_suite_path).hash_mapping_suite(
            with_version=version_in_cm)

        if mapping_suite_versioned_hash != metadata_json.get(MAPPING_SUITE_HASH):
            self.logger.error(event_message=EventMessage(
                message=f'The Mapping Suite hash digest ({mapping_suite_versioned_hash}) and the Version from the '
                        f'Conceptual Mappings ({version_in_cm}) '
                        f'does not correspond to the ones in the metadata.json file '
                        f'({metadata_json.get(MAPPING_SUITE_HASH)}, {metadata_json.get(VERSION_KEY)}). '
                        f'Consider increasing the version and regenerating the metadata.json'),
                settings=self.log_settings)
            success = False

        return success

    def is_valid(self) -> bool:
        validate_core_structure: bool = self.validate_core_structure()
        validate_expanded_structure: bool = self.validate_expanded_structure()
        validate_output_structure: bool = self.validate_output_structure()
        check_metadata_consistency: bool = self.check_metadata_consistency()
        check_for_changes_by_version: bool = self.check_for_changes_by_version()

        return \
            validate_core_structure \
            and validate_expanded_structure \
            and validate_output_structure \
            and check_metadata_consistency \
            and check_for_changes_by_version
