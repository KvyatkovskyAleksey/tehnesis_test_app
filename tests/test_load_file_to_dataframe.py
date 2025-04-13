import pytest
from aiogram.types import Document

from app import uploaded_file_type_is_correct, get_file_extension


@pytest.fixture
def correct_document():
    return Document(file_name="test.xlsx", file_unique_id="unique_id", file_id="1")


@pytest.fixture
def incorrect_document():
    return Document(file_name="test.txt", file_unique_id="unique_id", file_id="1")


def test_get_file_extension():
    doc1 = Document(file_name="example.csv", file_unique_id="unique_id", file_id="1")
    doc2 = Document(
        file_name="example.extension", file_unique_id="unique_id", file_id="1"
    )
    assert get_file_extension(doc1) == "csv"
    assert get_file_extension(doc2) == "extension"


@pytest.mark.unit
def test_uploaded_file_type_is_correct_true(correct_document):
    assert uploaded_file_type_is_correct(correct_document) is True


@pytest.mark.unit
def test_uploaded_file_type_is_correct_false(incorrect_document):
    assert uploaded_file_type_is_correct(incorrect_document) is False
