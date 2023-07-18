from typing import Dict, Union

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

from goals.models import Goal, BoardParticipant
from tests.factories import BoardFactory, BoardParticipantFactory, CategoryFactory


@pytest.mark.django_db
class TestGoalCreateView:
    url: str = reverse("goals:goal_create")

    def test_goal_create_owner_moderator(self, auth_client, user, due_date) -> None:
        board = BoardFactory()
        category = CategoryFactory(board=board)
        BoardParticipantFactory(board=board, user=user)

        create_data: Dict[str, Union[str, int]] = {
            "category": category.pk,
            "title": "New goal",
            "due_date": due_date,
        }

        response: Response = auth_client.post(self.url, data=create_data)
        created_goal = Goal.objects.filter(
            user=user, category=category, title=create_data["title"]
        ).exists()

        assert response.status_code == status.HTTP_201_CREATED, "goal not created"
        assert created_goal, "not exists"

    def test_goal_create_deny(self, client) -> None:
        response: Response = client.post(self.url)

        assert response.status_code == status.HTTP_403_FORBIDDEN, "no access"
