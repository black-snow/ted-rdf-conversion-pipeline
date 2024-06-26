#!/usr/bin/python3

# metadata_transformer.py
# Date:  02/03/2022
# Author: Kolea PLESCO
# Email: kalean.bl@gmail.com

"""
This module provides functionalities to archive files
"""

import abc
import os
from pathlib import Path
from typing import List
from zipfile import ZipFile, ZIP_DEFLATED

ARCHIVE_ZIP_FORMAT = "zip"
ARCHIVE_ZIP_COMPRESSION = ZIP_DEFLATED
ARCHIVE_DEFAULT_FORMAT = ARCHIVE_ZIP_FORMAT
ARCHIVE_MODE_WRITE = 'w'
ARCHIVE_MODE_APPEND = 'a'
ARCHIVE_MODE = ARCHIVE_MODE_WRITE


class ArchiverABC(abc.ABC):
    """
    This abstract class provides methods definitions and infos for available archivers
    """

    @abc.abstractmethod
    def process_archive(self, archive_name: Path, files: List[Path], mode: str) -> Path:
        """
        This method adds the files (based on provided archive mode) to archive
        """


class ZipArchiver(ArchiverABC):
    def process_archive(self, archive_name: Path, files: List[Path], mode: str = ARCHIVE_MODE) -> Path:
        with ZipFile(archive_name, mode=mode, compression=ARCHIVE_ZIP_COMPRESSION) as archive:
            for file in files:
                if os.path.isfile(file):
                    archive.write(file, os.path.basename(file))
            archive.close()
        return archive_name
