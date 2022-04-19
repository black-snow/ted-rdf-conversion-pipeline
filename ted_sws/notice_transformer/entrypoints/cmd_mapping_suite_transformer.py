#!/usr/bin/python3

import os
from pathlib import Path

import click

from ted_sws.core.adapters.cmd_runner import CmdRunner as BaseCmdRunner
from ted_sws.notice_transformer.services.notice_transformer import NoticeTransformer
from ted_sws import config
from ted_sws.data_manager.adapters.mapping_suite_repository import MappingSuiteRepositoryInFileSystem, \
    METADATA_FILE_NAME
from ted_sws.notice_transformer.adapters.rml_mapper import RMLMapper, SerializationFormat as RMLSerializationFormat, \
    TURTLE_SERIALIZATION_FORMAT

DEFAULT_MAPPINGS_PATH = 'mappings'
DEFAULT_OUTPUT_PATH = 'output'
CMD_NAME = "CMD_MAPPING_SUITE_TRANSFORMER"

"""
USAGE:
# transformer --help
"""


class CmdRunner(BaseCmdRunner):
    """
    Keeps the logic to be used by Notice Suite Transformer CMD
    """
    loggable: bool = True

    def __init__(
            self,
            mapping_suite_id,
            serialization_format_value,
            mappings_path=DEFAULT_MAPPINGS_PATH,
            output_path=DEFAULT_OUTPUT_PATH
    ):
        super().__init__(name=CMD_NAME)
        self.fs_repository_path = Path(os.path.realpath(mappings_path))
        self.output_path = output_path
        self.mapping_suite_id = mapping_suite_id
        self.serialization_format_value = serialization_format_value

    def is_mapping_suite(self, suite_id):
        suite_path = self.fs_repository_path / Path(suite_id)
        return os.path.isdir(suite_path) and any(f == METADATA_FILE_NAME for f in os.listdir(suite_path))

    def run(self):
        self.on_begin()
        if self.mapping_suite_id:
            self.transform(self.mapping_suite_id, self.serialization_format_value)
        else:
            for suite_id in os.listdir(self.fs_repository_path):
                self.transform(suite_id, self.serialization_format_value)
        self.on_end()

    def transform(self, mapping_suite_id, serialization_format_value):
        """
        Transforms the Test Mapping Suites (identified by mapping_suite_id)
        """
        self.log(
            "Running process for " + "\033[1;93m{}\033[00m".format("MappingSuite[" + mapping_suite_id + "]") + " ... "
        )

        if not self.is_mapping_suite(mapping_suite_id):
            self.log("\033[1;91m{}\033[00m".format("FAILED"))
            self.log("\033[1;91m {}\033[00m".format('FAILED') + " :: " + "Not a MappingSuite!")
            return False

        fs_mapping_suite_path = self.fs_repository_path / Path(mapping_suite_id)
        fs_output_path = fs_mapping_suite_path / Path(self.output_path)

        error = None
        try:
            mapping_suite_repository = MappingSuiteRepositoryInFileSystem(repository_path=self.fs_repository_path)
            mapping_suite = mapping_suite_repository.get(reference=mapping_suite_id)

            try:
                serialization_format = RMLSerializationFormat(serialization_format_value)
            except ValueError as e:
                raise ValueError('No such serialization format: %s' % serialization_format_value)

            notice_transformer = NoticeTransformer(mapping_suite=mapping_suite, rml_mapper=RMLMapper(
                rml_mapper_path=config.RML_MAPPER_PATH,
                serialization_format=serialization_format
            ), logger=self.get_logger())
            notice_transformer.transform_test_data(output_path=fs_output_path)
        except Exception as e:
            error = e

        suite_text = ":: " + mapping_suite_id
        if error:
            self.log("\033[1;91m{}\033[00m".format("FAILED"))
            self.log("\033[0;91m {}\033[00m".format(type(error).__name__ + ' :: ' + str(error)))
            self.log("\033[1;91m {}\033[00m".format('FAILED') + '  ' + suite_text)
            return False
        else:
            self.log("\033[1;92m{}\033[00m".format("DONE"))
            self.log("\033[1;92m {}\033[00m".format('SUCCESS') + '  ' + suite_text)
            return True


@click.command()
@click.argument('mapping-suite-id', nargs=1, required=False)
@click.argument('serialization-format', nargs=1, required=False, default=TURTLE_SERIALIZATION_FORMAT.value)
@click.option('--opt-mapping-suite-id', default=None,
              help='MappingSuite ID to be processed (leave empty to process all Mapping Suites).')
@click.option('--opt-serialization-format',
              help='Serialization format (turtle (default), nquads, trig, trix, jsonld, hdt).')
@click.option('--opt-mappings-path', default=DEFAULT_MAPPINGS_PATH)
@click.option('--opt-output-path', default=DEFAULT_OUTPUT_PATH)
def main(mapping_suite_id, serialization_format, opt_mapping_suite_id, opt_serialization_format, opt_mappings_path,
         opt_output_path):
    """
    Transforms the Test Mapping Suites (identified by mapping-suite-id).
    If no mapping-suite-id is provided, all mapping suites from mappings directory will be processed.
    """
    if opt_mapping_suite_id:
        mapping_suite_id = opt_mapping_suite_id
    if opt_serialization_format:
        serialization_format = opt_serialization_format
    mappings_path = opt_mappings_path
    output_path = opt_output_path

    cmd = CmdRunner(
        mapping_suite_id=mapping_suite_id,
        serialization_format_value=serialization_format,
        mappings_path=mappings_path,
        output_path=output_path
    )
    cmd.run()


if __name__ == '__main__':
    main()