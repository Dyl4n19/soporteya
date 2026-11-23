import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient


@pytest.fixture
def api(db):
    user = User.objects.create_user("supervisor", password="test12345", email="supervisor@test.cl")
    user.groups.add(Group.objects.create(name="SUPERVISOR"))
    client = APIClient()
    client.force_authenticate(user)
    return client
