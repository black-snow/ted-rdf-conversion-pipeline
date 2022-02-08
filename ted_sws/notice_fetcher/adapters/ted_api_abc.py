import abc
from datetime import date
from typing import List


class DocumentSearchABC(abc.ABC):
    @abc.abstractmethod
    def get_by_id(self, document_id: str) -> str:
        """
        Method to get a document content by ID
        :param document_id:
        :return:
        """

    @abc.abstractmethod
    def get_by_range_date(self, start_date: date, end_date: date) -> List[str]:
        """
        Method to get a documents content by passing a date range
        :param start_date:
        :param end_date:
        :return:
        """

    @abc.abstractmethod
    def get_by_wildcard_date(self, wildcard_date: str) -> List[str]:
        """
        Method to get a documents content by passing a wildcard date
        :param wildcard_date:
        :return:
        """

    @abc.abstractmethod
    def get_by_query(self, query: dict) -> List[str]:
        """
        Method to get a documents content by passing a search query
        :param query:
        :return:
        """
