from django.test import TestCase
from django.urls import reverse

from .models import ServiceReport, ServiceTask, ServiceTaskItem


class ServiceViewsTests(TestCase):
    def setUp(self):
        self.active_task = ServiceTask.objects.create(
            task_type='refill',
            requester_name='Іван Петренко',
            department='Бухгалтерія',
            description='Потрібна заправка',
            is_completed=False,
        )
        self.completed_task = ServiceTask.objects.create(
            task_type='repair',
            requester_name='Оксана Іванчук',
            department='Кадри',
            description='Принтер не друкує',
            is_completed=True,
        )
        self.active_item = ServiceTaskItem.objects.create(
            task=self.active_task,
            item_name='Картридж Canon 725/ HP [CE285A]',
            quantity=3,
        )

    def _create_payload(self):
        return {
            'task_type': 'refill',
            'requester_name': 'Петро Зінич',
            'department': 'Коломийський відділ',
            'date_received': '2025-03-01',
            'date_sent': '',
            'date_back_from_service': '',
            'date_returned': '',
            'description': 'Створено через тест',
            'is_completed': '',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-item_name': 'Інше',
            'items-0-quantity': '2',
            'items-0-custom_name': 'HP LaserJet 1102',
            'items-0-note': 'не бере папір',
            'items-0-id': '',
            'items-0-task': '',
        }

    def test_service_list_filters_by_status(self):
        active_response = self.client.get(reverse('service_list'), {'filter': 'active'})
        completed_response = self.client.get(reverse('service_list'), {'filter': 'completed'})

        self.assertEqual(active_response.status_code, 200)
        self.assertContains(active_response, 'Іван Петренко')
        self.assertNotContains(active_response, 'Оксана Іванчук')

        self.assertEqual(completed_response.status_code, 200)
        self.assertContains(completed_response, 'Оксана Іванчук')
        self.assertNotContains(completed_response, 'Іван Петренко')

    def test_service_create_creates_task_with_items(self):
        response = self.client.post(reverse('service_create'), data=self._create_payload())

        self.assertEqual(response.status_code, 302)
        created_task = ServiceTask.objects.get(requester_name='Петро Зінич')
        created_item = created_task.items.get()
        self.assertEqual(created_item.item_name, 'Інше')
        self.assertEqual(created_item.quantity, 2)
        self.assertEqual(created_item.custom_name, 'HP LaserJet 1102')

    def test_item_receive_ajax_splits_item(self):
        response = self.client.get(
            reverse('item_receive', args=[self.active_item.pk]),
            {'qty': '1'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['success'])
        self.assertTrue(payload['is_split'])

        self.active_item.refresh_from_db()
        self.assertEqual(self.active_item.quantity, 2)
        self.assertEqual(self.active_task.items.count(), 2)

    def test_item_return_marks_task_completed_when_all_items_returned(self):
        response = self.client.get(reverse('item_return', args=[self.active_item.pk]))

        self.assertEqual(response.status_code, 302)
        self.active_item.refresh_from_db()
        self.active_task.refresh_from_db()
        self.assertIsNotNone(self.active_item.date_returned_to_user)
        self.assertTrue(self.active_task.is_completed)
        self.assertIsNotNone(self.active_task.date_returned)

    def test_save_report_sets_date_sent_and_creates_report(self):
        response = self.client.post(reverse('save_report'))

        self.assertEqual(response.status_code, 302)
        report = ServiceReport.objects.latest('id')
        self.assertIn(self.active_task, report.tasks.all())
        self.active_task.refresh_from_db()
        self.assertIsNotNone(self.active_task.date_sent)

    def test_get_last_department_returns_found_for_existing_requester(self):
        response = self.client.get(reverse('get_last_department'), {'name': 'Іван Петренко'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['found'])
        self.assertEqual(payload['department'], 'Бухгалтерія')
