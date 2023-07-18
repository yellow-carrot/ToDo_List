from datetime import datetime
from typing import Dict

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

from goals.models import Board
from goals.serializers import BoardCreateSerializer, BoardSerializer
from tests.factories import BoardParticipantFactory, BoardFactory


@pytest.mark.django_db
class TestBoardView:
    url: str = reverse('goals:board_list')

    def test_board_create(self, client, auth_client):
        url = reverse('goals:board_create')

        expected_response = {
            'created': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'title': 'test board',
            'is_deleted': False
        }
        response = client.post(path=url, data=expected_response)

        assert response.status_code == status.HTTP_201_CREATED
        board = Board.objects.get()
        assert board.title == expected_response['title']
        assert response.data['is_deleted'] == expected_response['is_deleted']

    def test_active_board_list_participant(self, auth_client, user) -> None:
        active_boards = BoardFactory.create_batch(size=5)

        for board in active_boards:
            BoardParticipantFactory(board=board, user=user)

        expected_response: Dict = BoardCreateSerializer(active_boards, many=True).data
        response: Response = auth_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK, "failed"
        assert response.data == expected_response, "doesnt match"

    def test_deleted_board_list_participant(self, auth_client, user) -> None:
        deleted_boards = BoardFactory.create_batch(size=5, is_deleted=True)

        for board in deleted_boards:
            BoardParticipantFactory(board=board, user=user)

        unexpected_response: Dict = BoardCreateSerializer(
            deleted_boards, many=True
        ).data
        response: Response = auth_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK, "failed"
        assert not response.data == unexpected_response, "got deleted boards"

    def test_board_list_not_participant(self, auth_client) -> None:
        boards = BoardFactory.create_batch(size=5)

        for board in boards:
            BoardParticipantFactory(board=board)

        unexpected_response: Dict = BoardCreateSerializer(boards, many=True).data
        response: Response = auth_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK, "failed"
        assert not response.data == unexpected_response, "got another boards"

    def test_board_list_deny(self, client) -> None:
        response: Response = client.get(self.url)

        assert (
                response.status_code == status.HTTP_403_FORBIDDEN
        ), "no access"

    def test_active_board_retrieve_participant(self, auth_client, user) -> None:
        board = BoardFactory()
        BoardParticipantFactory(board=board, user=user)
        url: str = reverse("goals:board_pk", kwargs={"pk": board.id})

        expected_response: Dict = BoardSerializer(board).data
        response: Response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK, "failed"
        assert response.data == expected_response, "not exact board"

    def test_deleted_board_retrieve_participant(self, auth_client, user) -> None:
        board = BoardFactory(is_deleted=True)
        BoardParticipantFactory(board=board, user=user)
        url: str = reverse("goals:board_pk", kwargs={"pk": board.id})

        unexpected_response: Dict = BoardSerializer(board).data
        response: Response = auth_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND, "not 404"
        assert not response.data == unexpected_response, "got deleted"

    def test_board_retrieve_not_participant(self, auth_client) -> None:

        board = BoardFactory(is_deleted=True)
        BoardParticipantFactory(board=board)
        url: str = reverse("goals:board_pk", kwargs={"pk": board.id})

        unexpected_response: Dict = BoardSerializer(board).data
        response: Response = auth_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND, "not 404"
        assert not response.data == unexpected_response, "got another"

    def test_board_retrieve_deny(self, client) -> None:

        url: str = reverse("goals:board_pk", kwargs={"pk": 1})
        response: Response = client.get(url)

        assert (
                response.status_code == status.HTTP_403_FORBIDDEN
        ), "no access"
