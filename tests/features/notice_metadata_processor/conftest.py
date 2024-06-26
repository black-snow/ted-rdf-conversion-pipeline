import pytest

from ted_sws import config
from ted_sws.data_manager.adapters.mapping_suite_repository import MappingSuiteRepositoryInFileSystem, \
    MappingSuiteRepositoryMongoDB
from ted_sws.notice_metadata_processor.services.metadata_normalizer import normalise_notice
from tests import TEST_DATA_PATH
from tests.fakes.fake_repository import FakeNoticeRepository


@pytest.fixture
def notice_identifier():
    return "67623-2022"


@pytest.fixture
def api_end_point():
    return config.TED_API_URL


@pytest.fixture
def fake_notice_storage():
    return FakeNoticeRepository()


@pytest.fixture
def notice_eligibility_repository_path():
    return TEST_DATA_PATH / "notice_transformer" / "test_repository"


@pytest.fixture
def normalised_notice(notice_2020):
    notice = notice_2020.copy()
    normalise_notice(notice=notice)
    return notice

@pytest.fixture
def normalised_eForm_notice(indexed_eform_notice_622690):
    notice = indexed_eform_notice_622690.copy()
    normalise_notice(notice=notice)
    return notice


@pytest.fixture
def mapping_suite_repository_with_mapping_suite(notice_eligibility_repository_path):
    mapping_suite_repository = MappingSuiteRepositoryInFileSystem(repository_path=notice_eligibility_repository_path)
    return mapping_suite_repository


@pytest.fixture
def clean_mapping_suite_repository(mongodb_client):
    mapping_suite_repository = MappingSuiteRepositoryMongoDB(mongodb_client=mongodb_client)
    return mapping_suite_repository
