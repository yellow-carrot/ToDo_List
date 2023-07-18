from typing import Dict

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

from goals.serializers import GoalCategorySerializer, BoardCreateSerializer
from tests.factories import BoardFactory, CategoryFactory, BoardParticipantFactory


@pytest.mark.django_db
class TestCategoryListView:
    url: str = reverse("goals:category_list")

    def test_active_category_list_participant(self, auth_client, user) -> None:
        board = BoardFactory()
        active_categories = CategoryFactory.create_batch(size=5, board=board)
        BoardParticipantFactory(board=board, user=user)

        expected_response: Dict = GoalCategorySerializer(
            active_categories, many=True
        ).data
        sorted_expected_response: list = sorted(
            expected_response, key=lambda x: x["title"]
        )
        response = auth_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK, "no access"
        assert response.json() == sorted_expected_response, "lists of categories arent match"

    def test_deleted_category_list_participant(self, auth_client, user) -> None:
        board = BoardFactory()
        deleted_categories = CategoryFactory.create_batch(
            size=5, board=board, is_deleted=True
        )
        BoardParticipantFactory(board=board, user=user)

        unexpected_response: Dict = GoalCategorySerializer(
            deleted_categories, many=True
        ).data
        response = auth_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK, "no access"
        assert not response.json() == unexpected_response, "got deleted"

    def test_category_list_not_participant(self, auth_client) -> None:
        board = BoardFactory()
        categories = CategoryFactory.create_batch(size=5, board=board)
        BoardParticipantFactory(board=board)

        unexpected_response: Dict = BoardCreateSerializer(categories, many=True).data
        response = auth_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK, "no access"
        assert not response.json() == unexpected_response, "got another categories"

    def test_category_create_deny(self, client) -> None:
        response: Response = client.post(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN, "no access"
