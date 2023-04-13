import tempfile
from pathlib import Path
from typing import List
from urllib.request import urlopen

from deepdiff import DeepDiff
from jinja2 import Environment, PackageLoader
from json2html import json2html
from pydantic.utils import deep_update

from ted_sws import config
from ted_sws.core.model.transform import ConceptualMapping, ConceptualMappingRule, ConceptualMappingRemark, \
    ConceptualMappingResource, ConceptualMappingRMLModule
from ted_sws.core.model.transform import ConceptualMappingDiff, ConceptualMappingDiffMetadata, ConceptualMappingDiffData
from ted_sws.data_manager.adapters.mapping_suite_repository import MS_TRANSFORM_FOLDER_NAME, \
    MS_CONCEPTUAL_MAPPING_FILE_NAME
from ted_sws.mapping_suite_processor.services.conceptual_mapping_reader import mapping_suite_read_conceptual_mapping

TEMPLATES = Environment(loader=PackageLoader("ted_sws.mapping_suite_processor.resources", "templates"))
CONCEPTUAL_MAPPINGS_DIFF_HTML_REPORT_TEMPLATE = "conceptual_mappings_diff_report.jinja2"

GITHUB_CONCEPTUAL_MAPPINGS_PATH = "{GITHUB_BASE}/raw/{GIT_BRANCH}/mappings/{MAPPING_SUITE_ID}/" + \
                                  MS_TRANSFORM_FOLDER_NAME + "/" + MS_CONCEPTUAL_MAPPING_FILE_NAME

DEFAULT_REPORT_FILE_NAME = "cm_diff"
DIFF_VALUE_CONTEXT_KEY = "__CONTEXT__"

DIFF_METADATA_TAB = "metadata"
DIFF_RULES_TAB = "rules"
DIFF_MAPPING_REMARKS_TAB = "mapping_remarks"
DIFF_RESOURCES_TAB = "resources"
DIFF_RML_MODULES_TAB = "rml_modules"
DIFF_CL1_ROLES_TAB = "cl1_roles"
DIFF_CL2_ORGANISATIONS_TAB = "cl2_organisations"


class ConceptualMappingDiffDataTransformer:
    data: dict
    tabs: dict = {
        DIFF_METADATA_TAB: {},
        DIFF_RULES_TAB: {},
        DIFF_MAPPING_REMARKS_TAB: {},
        DIFF_RESOURCES_TAB: {},
        DIFF_RML_MODULES_TAB: {},
        DIFF_CL1_ROLES_TAB: {},
        DIFF_CL2_ORGANISATIONS_TAB: {}
    }
    labels: dict
    mapping1: ConceptualMapping
    mapping2: ConceptualMapping
    context_mapping: ConceptualMapping

    item_key_flattenizer: str = "|"

    def __init__(self, data, mapping1: ConceptualMapping, mapping2: ConceptualMapping):
        self.data = data
        self.mapping1 = mapping1
        self.mapping2 = mapping2
        self.context_mapping = self.mapping2
        self.init_labels()
        self.init_tabs()
        self.process_tabs_data()

    @classmethod
    def init_labels(cls):
        cls.labels = {
            "tabs": {
                DIFF_METADATA_TAB: "Metadata",
                DIFF_RULES_TAB: "Rules",
                DIFF_MAPPING_REMARKS_TAB: "Remarks",
                DIFF_RESOURCES_TAB: "Resources",
                DIFF_RML_MODULES_TAB: "RML Modules",
                DIFF_CL1_ROLES_TAB: "CL1 Roles",
                DIFF_CL2_ORGANISATIONS_TAB: "CL2 Organisations"
            },
            "actions": {
                "set_item_added": "Set Added",
                "set_item_removed": "Set Removed",
                "iterable_item_removed": "Removed",
                "iterable_item_added": "Added",
                "iterable_item_moved": "Moved",
                "values_changed": "Changed"
            },
            "fields": {
                "identifier": "Identifier",
                "title": "Title",
                "description": "Description",
                "mapping_version": "Mapping Version",
                "epo_version": "EPO version",
                "base_xpath": "Base XPath",
                "metadata_constraints": "Metadata constraints",
                "eforms_subtype": "eForms Subtype",
                "start_date": "Start Date",
                "end_date": "End Date",
                "min_xsd_version": "Min XSD Version",
                "max_xsd_version": "Max XSD Version",
                "standard_form_field_id": "Standard Form Field ID (M)",
                "standard_form_field_name": "Standard Form Field Name (M)",
                "eform_bt_id": "eForm BT-ID (O)",
                "eform_bt_name": "eForm BT Name (O)",
                "field_xpath": "Field XPath (M)",
                "field_xpath_condition": "Field XPath condition (M)",
                "class_path": "Class path (M)",
                "property_path": "Property path (M)",
                "triple_fingerprint": "Triple Fingerprint",
                "fragment_fingerprint": "Fragment Fingerprint",
                "file_name": "File name",
                "old_value": "Old value",
                "new_value": "New value",
                "field_value": "Field Value (in XML)",
                "mapping_reference": "Mapping Reference (in ePO)",
                "super_type": "SuperType",
                "xml_path_fragment": "XML PATH Fragment"
            }
        }

    def init_tabs(self):
        for action in self.data:
            action_items = self.unflatten(self.data[action])
            for tab in action_items:
                if tab not in self.tabs:
                    continue
                if action not in self.tabs[tab]:
                    self.tabs[tab][action] = {}
                self.tabs[tab][action] = deep_update(self.tabs[tab][action], action_items[tab])

    def process_tabs_data(self):
        self.process_rules_tab()
        self.process_mapping_remarks_tab()
        self.process_resources_tab()
        self.process_rml_modules_tab()

    def process_rules_tab(self):
        cm_rules_len = len(self.context_mapping.rules)
        for action in self.tabs[DIFF_RULES_TAB]:
            for row_idx in self.tabs[DIFF_RULES_TAB][action]:
                idx = int(row_idx)
                if idx < cm_rules_len:
                    cm_row: ConceptualMappingRule = self.context_mapping.rules[idx]
                    context = [cm_row.standard_form_field_id, cm_row.standard_form_field_name]
                    self.tabs[DIFF_RULES_TAB][action][row_idx][DIFF_VALUE_CONTEXT_KEY] = context

    def process_mapping_remarks_tab(self):
        cm_mapping_remarks_len = len(self.context_mapping.mapping_remarks)
        for action in self.tabs[DIFF_MAPPING_REMARKS_TAB]:
            for row_idx in self.tabs[DIFF_MAPPING_REMARKS_TAB][action]:
                idx = int(row_idx)
                if idx < cm_mapping_remarks_len:
                    cm_row: ConceptualMappingRemark = self.context_mapping.mapping_remarks[idx]
                    context = [cm_row.standard_form_field_id, cm_row.standard_form_field_name]
                    self.tabs[DIFF_MAPPING_REMARKS_TAB][action][row_idx][DIFF_VALUE_CONTEXT_KEY] = context

    def process_resources_tab(self):
        cm_resources_len = len(self.context_mapping.resources)
        for action in self.tabs[DIFF_RESOURCES_TAB]:
            for row_idx in self.tabs[DIFF_RESOURCES_TAB][action]:
                idx = int(row_idx)
                if idx < cm_resources_len:
                    cm_row: ConceptualMappingResource = self.context_mapping.resources[idx]
                    context = [cm_row.file_name]
                    self.tabs[DIFF_RESOURCES_TAB][action][row_idx][DIFF_VALUE_CONTEXT_KEY] = context

    def process_rml_modules_tab(self):
        cm_rml_modules_len = len(self.context_mapping.rml_modules)
        for action in self.tabs[DIFF_RML_MODULES_TAB]:
            for row_idx in self.tabs[DIFF_RML_MODULES_TAB][action]:
                idx = int(row_idx)
                if idx < cm_rml_modules_len:
                    cm_row: ConceptualMappingRMLModule = self.context_mapping.rml_modules[idx]
                    context = [cm_row.file_name]
                    self.tabs[DIFF_RML_MODULES_TAB][action][row_idx][DIFF_VALUE_CONTEXT_KEY] = context

    @classmethod
    def normalize_item_key(cls, k):
        return cls.item_key_flattenizer.join(k.replace("'", "").split("root[", 1)[1].rsplit("]", 1)[0].split("]["))

    @classmethod
    def unflatten(cls, d):
        ud = {}
        for k, v in d.items():
            context = ud
            k = cls.normalize_item_key(k)
            for sub_key in k.split(cls.item_key_flattenizer)[:-1]:
                if sub_key not in context:
                    context[sub_key] = {}
                context = context[sub_key]
            context[k.split(cls.item_key_flattenizer)[-1]] = v
        return ud


def mapping_suite_diff_conceptual_mappings(mappings: List[ConceptualMapping]) -> dict:
    """
    This service return the difference between 2 Mapping Suite's conceptual mapping objects
    :param mappings:
    :return:
    """
    assert mappings and len(mappings) == 2
    diff: ConceptualMappingDiff = ConceptualMappingDiff()
    diff.metadata = ConceptualMappingDiffMetadata(
        defaults={
            "branch": "local",
            "conceptual_mapping": MS_TRANSFORM_FOLDER_NAME + "/" + MS_CONCEPTUAL_MAPPING_FILE_NAME
        },
        metadata=[
            mappings[0].metadata.dict(),
            mappings[1].metadata.dict()
        ]
    )
    mapping1: dict = mappings[0].dict()
    mapping2: dict = mappings[1].dict()

    diff.data = transform_conceptual_mappings_diff_data(ConceptualMappingDiffData(
        original=DeepDiff(mapping1, mapping2, ignore_order=False)
    ), mapping1=mappings[0], mapping2=mappings[1])
    return diff.dict()


def mapping_suite_diff_files_conceptual_mappings(filepaths: List[Path]) -> dict:
    """
    This service return the difference between 2 Mapping Suite's conceptual mapping objects
    based on their filepaths
    :param filepaths:
    :return:
    """
    assert filepaths and len(filepaths) == 2
    assert filepaths[0].is_file()
    assert filepaths[1].is_file()
    return mapping_suite_diff_conceptual_mappings([
        mapping_suite_read_conceptual_mapping(filepaths[0]),
        mapping_suite_read_conceptual_mapping(filepaths[1])
    ])


def mapping_suite_diff_repo_conceptual_mappings(branch_or_tag_name: List[str], mapping_suite_id: List[str],
                                                filepath: Path = None) -> dict:
    """
    This service return the difference between 2 Mapping Suite's conceptual mapping objects
    based on their repository branch

    1) repo vs file
    2) repo vs repo

    :param mapping_suite_id:
    :param branch_or_tag_name:
    :param filepath:
    :return:
    """

    assert branch_or_tag_name and len(branch_or_tag_name) > 0
    assert mapping_suite_id and len(mapping_suite_id) > 0

    git_extension = ".git"
    github_base = config.GITHUB_TED_SWS_ARTEFACTS_URL
    if github_base.endswith(git_extension):
        github_base = github_base[:-(len(git_extension))]

    url_resource = urlopen(GITHUB_CONCEPTUAL_MAPPINGS_PATH.format(
        GITHUB_BASE=github_base,
        GIT_BRANCH=branch_or_tag_name[0],
        MAPPING_SUITE_ID=mapping_suite_id[0]
    ))
    temp_file1 = tempfile.NamedTemporaryFile()
    temp_file1.write(url_resource.read())
    filepath1 = Path(temp_file1.name)

    if filepath:
        assert filepath.is_file()
        filepath2 = filepath
    else:
        if len(branch_or_tag_name) < 2:
            branch_or_tag_name.append(branch_or_tag_name[0])

        if len(mapping_suite_id) < 2:
            mapping_suite_id.append(mapping_suite_id[0])

        url_resource = urlopen(GITHUB_CONCEPTUAL_MAPPINGS_PATH.format(
            GITHUB_BASE=github_base,
            GIT_BRANCH=branch_or_tag_name[1],
            MAPPING_SUITE_ID=mapping_suite_id[1]
        ))
        temp_file2 = tempfile.NamedTemporaryFile()
        temp_file2.write(url_resource.read())
        filepath2 = Path(temp_file2.name)

    return mapping_suite_diff_files_conceptual_mappings([filepath1, filepath2])


def transform_conceptual_mappings_diff_data(diff_data: ConceptualMappingDiffData, mapping1: ConceptualMapping,
                                            mapping2: ConceptualMapping):
    diff_transformer = ConceptualMappingDiffDataTransformer(data=diff_data.original, mapping1=mapping1,
                                                            mapping2=mapping2)
    diff_data.transformed = {
        "labels": diff_transformer.labels,
        "tabs": diff_transformer.tabs
    }
    return diff_data


def generate_conceptual_mappings_diff_html_report(diff: ConceptualMappingDiff):
    diff.data.html = json2html.convert(
        json=diff.data.original,
        table_attributes='class="display dataTable heading"',
        clubbing=True
    )
    html_report = TEMPLATES.get_template(CONCEPTUAL_MAPPINGS_DIFF_HTML_REPORT_TEMPLATE).render(diff)
    return html_report


def generate_conceptual_mappings_diff_filename(diff: ConceptualMappingDiff, prefix: str = DEFAULT_REPORT_FILE_NAME,
                                               ext: str = None) -> str:
    filename: str = prefix
    cm1_metadata: dict = diff.metadata.metadata[0]
    if cm1_metadata:
        filename += f"_{cm1_metadata['identifier']}_v{cm1_metadata['mapping_version']}"
    cm2_metadata: dict = diff.metadata.metadata[1]
    if cm2_metadata:
        if cm1_metadata:
            filename += "_vs"
        filename += f"_{cm2_metadata['identifier']}_v{cm2_metadata['mapping_version']}"
    if ext:
        filename += ext
    return filename
