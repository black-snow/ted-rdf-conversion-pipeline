import copy
import json
import pathlib
from datetime import date
from typing import List
from ted_sws.notice_fetcher.adapters.ted_api_abc import DocumentSearchABC, RequestAPI


def get_fake_api_response() -> dict:
    path = pathlib.Path(__file__).parent.parent / "test_data" / "notices" / "2021-OJS237-623049.json"
    return json.loads(path.read_text())


class FakeRequestAPI(RequestAPI):
    """

    """

    def __call__(self, api_url: str, api_query: dict) -> dict:
        """

        :param args:
        :param kwargs:
        :return:
        """
        return copy.deepcopy(get_fake_api_response())


class FakeTedDocumentSearch(DocumentSearchABC):
    """

    """

    def get_by_wildcard_date(self, wildcard_date: str) -> List[dict]:
        """

        :param wildcard_date:
        :return:
        """
        return [get_fake_api_response()]

    def get_by_id(self, document_id: str) -> dict:
        """

        :param document_id:
        :return:
        """
        return get_fake_api_response()

    def get_by_range_date(self, start_date: date, end_date: date) -> List[dict]:
        """

        :param start_date:
        :param end_date:
        :return:
        """
        return [get_fake_api_response()]

    def get_by_query(self, query: dict) -> List[dict]:
        """

        :param query:
        :return:
        """
        return [get_fake_api_response()]