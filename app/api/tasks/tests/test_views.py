from mock import patch
from freezegun import freeze_time

from django.core.exceptions import ObjectDoesNotExist
from django.http import QueryDict
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.tasks.views import TasksList
from backend.tasks.tests.utils import TaskTestUtils
from backend.users.tests.utils import UserTestUtils


class TasksListViewTestCase(APITestCase):
    endpoint_url = "/api/v1/tasks/list/"
    UUID = "ea0ec33b-30e2-4601-9011-e35e1e2b5e0d"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = UserTestUtils.create_user(username="test_user")

    @property
    def service_mock_data(self):
        return [
            {
                "uuid": self.UUID,
                "title": "Test List View",
                "created": "01-01-2022 12:00:00",
                "last_updated": "01-01-2022 12:00:00",
                "status": "to_do",
            }
        ]

    def test_view_url(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.endpoint_url)
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIs(response.resolver_match.func.view_class, TasksList)

    def test_post_method_gets_405_error(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.endpoint_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_method_gets_405_error(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.endpoint_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_method_gets_405_error(self):
        self.client.force_authenticate(self.user)
        response = self.client.put(self.endpoint_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_not_authenticated_user_gets_401_error(self):
        response = self.client.get(self.endpoint_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("api.tasks.views.list_tasks_for_user")
    def test_tasks_list(self, mock_service):
        mock_service.return_value = self.service_mock_data

        self.client.force_authenticate(self.user)
        response = self.client.get(self.endpoint_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertListEqual(response.json().get("results"), self.service_mock_data)

    @patch("api.tasks.views.list_tasks_for_user")
    def test_tasks_list_service_only_called_once(self, mock_service):
        self.client.force_authenticate(self.user)
        self.client.get(self.endpoint_url)
        mock_service.assert_called_once_with(user_id=self.user.id, query_params=QueryDict())

    @freeze_time("2023-01-01 12:00:00")
    def test_integration_with_service(self):
        uuids = [
            "ea0ec33b-30e2-9999-9011-e35e1e2b5e0d",
            "ea0ec33b-30e2-5555-9011-e35e1e2b5e0d",
            "ea0ec33b-30e2-8888-9011-e35e1e2b5e0d",
        ]

        expected_tasks = [
            {
                "uuid": uuids[0],
                "title": "Task 1",
                "created": "01-01-2023 12:00:00",
                "last_updated": "01-01-2023 12:00:00",
                "status": "to_do",
            },
            {
                "uuid": uuids[1],
                "title": "Task 2",
                "created": "01-01-2023 12:00:00",
                "last_updated": "01-01-2023 12:00:00",
                "status": "to_do",
            },
        ]

        new_user = UserTestUtils.create_user(username="new_user")
        TaskTestUtils.create_task(uuid=uuids[0], title="Task 1", owner_id=self.user.id)
        TaskTestUtils.create_task(uuid=uuids[1], title="Task 2", owner_id=self.user.id)
        TaskTestUtils.create_task(uuid=uuids[2], title="Not listed", owner_id=new_user.id)

        self.client.force_authenticate(self.user)
        response = self.client.get(self.endpoint_url)
        results_list = response.json().get("results")
        for retrieved_task_data, expected_task_data in zip(results_list, expected_tasks):
            self.assertDictEqual(retrieved_task_data, expected_task_data)