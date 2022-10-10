import pytest

from tests import TEST_DATA_PATH


@pytest.fixture
def file_system_repository_path():
    return TEST_DATA_PATH / "notice_transformer" / "mapping_suite_processor_repository"


@pytest.fixture
def fake_test_mapping_suite_id() -> str:
    return "test_package"
