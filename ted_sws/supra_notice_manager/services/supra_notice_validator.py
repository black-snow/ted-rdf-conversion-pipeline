from datetime import datetime, date, time
from typing import List
from typing import Union

from pymongo import MongoClient

from ted_sws.core.model.supra_notice import SupraNoticeValidationReport, DailySupraNotice
from ted_sws.core.model.validation_report import ReportNotice
from ted_sws.data_manager.adapters.notice_repository import NoticeRepository
from ted_sws.data_manager.adapters.supra_notice_repository import DailySupraNoticeRepository
from ted_sws.event_manager.services.log import log_technical_error
from ted_sws.notice_fetcher.adapters.ted_api import TedAPIAdapter, RequestAPI, TedRequestAPI
from ted_sws.notice_validator.services.validation_summary_runner import generate_validation_summary_report_notices

day_type = Union[datetime, date]

SUPRA_NOTICE_NOT_FOUND_ERROR = "SupraNotice not found in Database!"


def validate_and_update_daily_supra_notice(ted_publication_date: day_type, mongodb_client: MongoClient,
                                           request_api: RequestAPI = None):
    if request_api is None:
        request_api = TedRequestAPI()

    if isinstance(ted_publication_date, date):
        ted_publication_date = datetime.combine(ted_publication_date, time())

    repo = DailySupraNoticeRepository(mongodb_client=mongodb_client)
    supra_notice: DailySupraNotice = repo.get(reference=ted_publication_date)

    if not supra_notice:
        raise ValueError(SUPRA_NOTICE_NOT_FOUND_ERROR)

    fetched_notice_ids_list = supra_notice.notice_ids or []
    fetched_notice_ids = set(fetched_notice_ids_list)

    ted_api_adapter: TedAPIAdapter = TedAPIAdapter(request_api=request_api)
    query = {"query": f"PD={ted_publication_date.strftime('%Y%m%d*')}"}
    documents = ted_api_adapter.get_by_query(query=query, result_fields={"fields": ["ND"]}, load_content=False)
    api_notice_ids_list = [document["ND"] for document in documents] if documents and len(documents) else []
    api_notice_ids = set(api_notice_ids_list)

    validation_report = supra_notice.validation_report or SupraNoticeValidationReport(object_data="")
    missing_notice_ids = api_notice_ids - fetched_notice_ids
    if len(missing_notice_ids):
        validation_report.missing_notice_ids = list(missing_notice_ids)
        log_technical_error(message=f"Supra notice for date [{ted_publication_date}] don't fetch notices with ids=[{missing_notice_ids}]")

    supra_notice.validation_report = validation_report
    repo.update(daily_supra_notice=supra_notice)


def summary_validation_for_daily_supra_notice(ted_publication_date: day_type, mongodb_client: MongoClient):
    if isinstance(ted_publication_date, date):
        ted_publication_date = datetime.combine(ted_publication_date, time())

    repo = DailySupraNoticeRepository(mongodb_client=mongodb_client)
    supra_notice: DailySupraNotice = repo.get(reference=ted_publication_date)

    if not supra_notice:
        raise ValueError(SUPRA_NOTICE_NOT_FOUND_ERROR)

    notice_repository: NoticeRepository = NoticeRepository(mongodb_client=mongodb_client)
    notices: List[ReportNotice] = []

    for notice_id in supra_notice.notice_ids:
        notice: ReportNotice = ReportNotice(
            notice=notice_repository.get(reference=notice_id)
        )
        if notice:
            notices.append(notice)

    supra_notice.validation_summary = generate_validation_summary_report_notices(notices)
    # no notice_ids needed to be stored for supra_notice
    supra_notice.validation_summary.notices = []
    repo.update(daily_supra_notice=supra_notice)
