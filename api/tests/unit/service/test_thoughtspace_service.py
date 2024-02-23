import pytest
from unittest.mock import MagicMock
from api.service.thoughtspace_service import ThoughtSpaceService
from qdrant_client.http.models import ScoredPoint


@pytest.fixture
def thoughtspace_service():
    return ThoughtSpaceService()


def test_scored_point_to_message(thoughtspace_service):
    # Mocking a ScoredPoint object
    scored_point = ScoredPoint(
        id="test_id",
        payload={"content": "Test content", "voice": 1, "revisions": ["revision1", "revision2"]},
        score=0.95,
    )

    # Calling the method under test
    message = thoughtspace_service.scored_point_to_message(scored_point)

    # Assertions to verify the returned Message object
    assert message.id == "test_id"
    assert message.content == "Test content"
    assert message.similarity_score == 0.95
    assert message.voice == 1
    assert message.revisions_count == 2
