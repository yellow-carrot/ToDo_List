import datetime
import pytest
from rest_framework.test import APIClient

pytest_plugins = 'tests.factories'


@pytest.fixture()
def client() -> APIClient:
    return APIClient()


@pytest.fixture()
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture()
def another_user(user_factory):
    return user_factory.create()


@pytest.fixture()
def due_date():
    due_date: datetime = datetime.date.today() + datetime.timedelta(days=7)
    return due_date.strftime("%Y-%m-%d")