from datetime import datetime
from typing import List

from pymongo import MongoClient

from ted_sws import config
from ted_sws.core.model.notice import NoticeStatus
from ted_sws.data_manager.adapters.notice_repository import NoticeRepository

NOTICE_STATUS = "status"
FORM_NUMBER = "normalised_metadata.form_number"
XSD_VERSION = "normalised_metadata.xsd_version"
PUBLICATION_DATE = "normalised_metadata.publication_date"


def build_selector_mongodb_filter(notice_status: str, form_number: str = None,
                                  start_date: datetime = None, end_date: datetime = None,
                                  xsd_version: str = None) -> dict:
    mongodb_filter = {NOTICE_STATUS: notice_status}
    if form_number:
        mongodb_filter[FORM_NUMBER] = form_number
    if start_date and end_date:
        mongodb_filter[PUBLICATION_DATE] = {'$gte': start_date, '$lte': end_date}
    if xsd_version:
        mongodb_filter[XSD_VERSION] = xsd_version
    return mongodb_filter


def notice_ids_selector_by_status(notice_statuses: List[NoticeStatus], form_number: str = None,
                                  start_date: datetime = None, end_date: datetime = None,
                                  xsd_version: str = None) -> List[str]:
    mongodb_client = MongoClient(config.MONGO_DB_AUTH_URL)
    notice_repository = NoticeRepository(mongodb_client=mongodb_client)
    notice_ids = []
    for notice_status in notice_statuses:
        mongodb_filter = build_selector_mongodb_filter(notice_status=str(notice_status),
                                                       form_number=form_number,
                                                       start_date=start_date,
                                                       end_date=end_date,
                                                       xsd_version=xsd_version
                                                       )
        notice_ids.extend(list(notice_repository.collection.find(mongodb_filter)))

    return notice_ids
