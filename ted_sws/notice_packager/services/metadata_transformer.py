#!/usr/bin/python3

# metadata_transformer.py
# Date:  22/02/2022
# Author: Kolea PLESCO
# Email: kalean.bl@gmail.com

"""
This module provides transformers for notice metadata (original or normalized)
into data structures needed to render the templates.
This transformed metadata is what adapters expect.
"""

import datetime

from ted_sws.core.model.metadata import NormalisedMetadata
from ted_sws.notice_metadata_processor.model.metadata import ExtractedMetadata
from ted_sws.notice_packager.model.metadata import PackagerMetadata, METS_TYPE_CREATE, LANGUAGE, REVISION, BASE_WORK, \
    BASE_TITLE, METS_DMD_HREF, METS_DMD_ID, METS_TMD_ID, METS_TMD_HREF, METS_FILE_ID, METS_NOTICE_FILE_HREF

# This is used in pipeline
NORMALIZED_SEPARATOR = '_'

# This is used in TED API
DENORMALIZED_SEPARATOR = '-'

PROCUREMENT_PUBLIC = "procurement_public"
PROCUREMENT_NOTICE = "PROCUREMENT_NOTICE"


class MetadataTransformer:
    def __init__(self, notice_metadata: NormalisedMetadata):
        self.notice_metadata = notice_metadata

    def template_metadata(self, action: str = METS_TYPE_CREATE) -> PackagerMetadata:
        metadata = self.from_notice_metadata(self.notice_metadata)

        # here the custom and composed metadata properties are set
        metadata.mets.type = action
        metadata.mets.document_id = f"{metadata.work.identifier}_{action}"
        return metadata

    @classmethod
    def normalize_value(cls, value: str) -> str:
        """
        The initial (TED API) separator is replaced with pipeline's one.
        This is used when notice comes in from API
        :param value:
        :return:
        """
        return value.replace(DENORMALIZED_SEPARATOR, NORMALIZED_SEPARATOR)

    @classmethod
    def from_notice_metadata(cls, notice_metadata: NormalisedMetadata) -> PackagerMetadata:
        _date = datetime.datetime.now()
        _revision = REVISION

        metadata = PackagerMetadata()
        # NOTICE
        metadata.notice.id = cls.normalize_value(notice_metadata.notice_publication_number)
        metadata.notice.public_number_document = publication_notice_number(metadata.notice.id)
        metadata.notice.public_number_edition = publication_notice_year(
            notice_metadata) + filled_ojs_issue_number(notice_metadata.ojs_issue_number)

        # WORK
        publication_date = datetime.datetime.fromisoformat(notice_metadata.publication_date).strftime('%Y-%m-%d')
        metadata.work.identifier = publication_work_identifier(metadata.notice.id, notice_metadata)
        metadata.work.oj_identifier = publication_work_oj_identifier(metadata.notice.id, notice_metadata)
        metadata.work.cdm_rdf_type = PROCUREMENT_PUBLIC
        metadata.work.resource_type = PROCUREMENT_NOTICE
        metadata.work.date_document = publication_date
        metadata.work.uri = publication_notice_uri(metadata.notice.id, notice_metadata)
        metadata.work.title = {}
        if notice_metadata.title:
            metadata.work.title = {title[1]: title[0] for title in notice_metadata.title}
        metadata.work.dataset_version = _date.strftime('%Y%m%d') + '-' + _revision
        metadata.work.procurement_public_issued_by_country = notice_metadata.country_of_buyer
        # metadata.work.procurement_public_url_etendering = notice_metadata.uri_list

        # EXPRESSION
        metadata.expression.identifier = f"{metadata.work.identifier}.MUL"
        metadata.expression.title = {LANGUAGE: BASE_TITLE + " " + metadata.work.identifier}

        # MANIFESTATION
        metadata.manifestation.identifier = f"{metadata.expression.identifier}.rdf"
        metadata.manifestation.date_publication = publication_date

        # METS
        metadata.mets.dmd_href = METS_DMD_HREF.format(
            work_identifier=metadata.work.identifier,
            revision=metadata.mets.revision
        )
        metadata.mets.dmd_id = METS_DMD_ID.format(
            work_identifier=metadata.work.identifier,
            revision=metadata.mets.revision,
            dmd_idx="001"
        )
        metadata.mets.tmd_id = METS_TMD_ID.format(
            work_identifier=metadata.work.identifier,
            revision=metadata.mets.revision,
            tmd_idx="001"
        )
        metadata.mets.tmd_href = METS_TMD_HREF.format(
            work_identifier=metadata.work.identifier,
            revision=metadata.mets.revision
        )
        metadata.mets.file_id = METS_FILE_ID.format(
            work_identifier=metadata.work.identifier,
            revision=metadata.mets.revision,
            file_idx="001"
        )
        metadata.mets.notice_file_href = METS_NOTICE_FILE_HREF.format(
            work_identifier=metadata.work.identifier,
            revision=metadata.mets.revision
        )

        return metadata


def publication_notice_year(notice_metadata):
    return str(datetime.datetime.fromisoformat(notice_metadata.publication_date).year)


def publication_notice_number(notice_id):
    return notice_id.split(NORMALIZED_SEPARATOR)[0]


def publication_notice_uri(notice_id, notice_metadata):
    return f"{BASE_WORK}{publication_notice_year(notice_metadata)}/{notice_id}"


def publication_work_identifier(notice_id, notice_metadata):
    year = publication_notice_year(notice_metadata)
    number = publication_notice_number(notice_id)
    return f"{year}_{notice_metadata.ojs_type}_{filled_ojs_issue_number(notice_metadata.ojs_issue_number)}_{number}"


def publication_work_oj_identifier(notice_id, notice_metadata):
    year = publication_notice_year(notice_metadata)
    number = publication_notice_number(notice_id)
    return f"JOS_{year}_{filled_ojs_issue_number(notice_metadata.ojs_issue_number)}_R_{number}"


def filled_ojs_issue_number(ojs_issue_number: str) -> str:
    # just return the number without any preceding 0 (leaved the formula as it is in case of revert)
    return ojs_issue_number.split('/')[0].zfill(0)
