#!/usr/bin/python3

# conftest.py
# Date:  29/01/2022
# Author: Eugeniu Costetchi
# Email: costezki.eugen@gmail.com 

""" """

import pytest

from ted_sws.domain.model.manifestation import XMLManifestation, RDFManifestation, METSManifestation
from ted_sws.domain.model.notice import Notice, NoticeStatus


@pytest.fixture
def fetched_notice_data():
    ted_id = "ted_id1"
    source_url = "http://the.best.URL.com/in.the.world"
    original_metadata = {"key1": "value1"}
    xml_manifestation = XMLManifestation(object_data="XML manifestation content")

    return ted_id, source_url, original_metadata, xml_manifestation


def publicly_available_notice(fetched_notice_data):
    ted_id, source_url, original_metadata, xml_manifestation = fetched_notice_data
    notice = Notice(ted_id=ted_id, source_url=source_url, original_metadata=original_metadata,
                    xml_manifestation=xml_manifestation)
    notice.rdf_manifestation = RDFManifestation(object_data="RDF manifestation content")
    notice.mets_manifestation = METSManifestation(object_data="METS manifestation content")
    notice.status = NoticeStatus.PUBLICLY_AVAILABLE
    return notice
