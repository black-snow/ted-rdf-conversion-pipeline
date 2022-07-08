import os
from pathlib import Path

import click

from ted_sws.core.adapters.cmd_runner import CmdRunner as BaseCmdRunner, DEFAULT_MAPPINGS_PATH
from ted_sws.mapping_suite_processor.services.load_mapping_suite_output_into_triple_store import \
    load_mapping_suite_output_into_triple_store
from ted_sws.event_manager.adapters.logger import LOG_INFO_TEXT

DEFAULT_PACKAGE_FOLDER = '{mappings_path}/{mapping_suite_id}'
CMD_NAME = "CMD_TRIPLE_STORE_LOADER"

"""
USAGE:
# triple_store_loader --help
"""


class CmdRunner(BaseCmdRunner):
    """
    Keeps the logic to be used by Triple Store Loader CMD
    """

    def __init__(
            self,
            mapping_suite_id,
            package_folder,
            catalog_name
    ):
        super().__init__(name=CMD_NAME)
        self.mapping_suite_id = mapping_suite_id
        self.package_folder_path = Path(os.path.realpath(package_folder))
        self.catalog_name = catalog_name

    def run_cmd(self):
        self.log("Loading " + LOG_INFO_TEXT.format(self.mapping_suite_id) + " to Triple Store ... ")
        error = None
        try:
            load_mapping_suite_output_into_triple_store(
                package_folder_path=self.package_folder_path,
                allegro_catalog_name=self.catalog_name
            )
        except Exception as e:
            error = e

        return self.run_cmd_result(error)


def run(mapping_suite_id=None,
        opt_catalog_name=None,
        opt_mappings_folder=DEFAULT_MAPPINGS_PATH
        ):
    """
    This method will load the MappingSuite output into Triple Store
    :param mapping_suite_id:
    :param opt_catalog_name:
    :param opt_mappings_folder:
    :return:
    """

    package_folder = DEFAULT_PACKAGE_FOLDER.format(
        mappings_path=opt_mappings_folder,
        mapping_suite_id=mapping_suite_id
    )

    if opt_catalog_name:
        catalog_name = opt_catalog_name
    else:
        catalog_name = None

    cmd = CmdRunner(
        mapping_suite_id=mapping_suite_id,
        package_folder=package_folder,
        catalog_name=catalog_name
    )
    cmd.run()


@click.command()
@click.argument('mapping-suite-id', nargs=1, required=False)
@click.option('-c', '--opt-catalog-name', default=None)
@click.option('-m', '--opt-mappings-folder', default=DEFAULT_MAPPINGS_PATH)
def main(mapping_suite_id, opt_catalog_name, opt_mappings_folder):
    """
    Loads the MappingSuite output into Triple Store.
    """
    run(mapping_suite_id, opt_catalog_name, opt_mappings_folder)


if __name__ == '__main__':
    main()
