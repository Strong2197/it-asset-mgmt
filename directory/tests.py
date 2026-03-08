from django.test import TestCase
from django.urls import reverse

from .models import PhonebookEntry


class DirectoryViewsTests(TestCase):
    def setUp(self):
        self.entry1 = PhonebookEntry.objects.create(
            department='Івано-Франківський відділ',
            code='2610',
            email='if@example.com',
            chief_name='Іван Петренко',
            chief_phone='050-111-22-33',
            deputy_name='Оксана Іванчук',
            deputy_phone='050-444-55-66',
        )
        self.entry2 = PhonebookEntry.objects.create(
            department='Калуський відділ',
            code='2618',
            email='kalush@example.com',
            chief_name='Петро Зінич',
            chief_name='Петро Калуський',
            chief_phone='067-000-00-00',
        )

    def test_directory_list_filters_with_query(self):
        response = self.client.get(reverse('directory_list'), {'q': '2618'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Калуський відділ')
        self.assertNotContains(response, 'Івано-Франківський відділ')


    def test_directory_list_case_insensitive_for_cyrillic(self):
        response = self.client.get(reverse('directory_list'), {'q': 'ЗІНИЧ'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Калуський відділ')
        self.assertNotContains(response, 'Івано-Франківський відділ')

    def test_directory_list_ajax_returns_json(self):
        response = self.client.get(
            reverse('directory_list'),
            {'q': '2610'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        payload = response.json()
        self.assertIn('rows_html', payload)
        self.assertIn('Івано-Франківський відділ', payload['rows_html'])
        self.assertEqual(payload['total_count'], 1)


    def test_directory_list_ajax_finds_cyrillic_text(self):
        response = self.client.get(
            reverse('directory_list'),
            {'q': 'зінич'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('Калуський відділ', payload['rows_html'])
        self.assertEqual(payload['total_count'], 1)

    def test_directory_create_update_delete(self):
        create_response = self.client.post(
            reverse('directory_create'),
            data={
                'department': 'Надвірнянський відділ',
                'code': '2622',
                'email': 'nadv@example.com',
                'chief_name': 'Новий Керівник',
                'chief_position': 'Начальник відділу',
                'chief_phone': '099-999-99-99',
                'chief_ip': '3001',
                'deputy_name': '',
                'deputy_phone': '',
                'deputy_ip': '',
            },
        )
        self.assertEqual(create_response.status_code, 302)
        created = PhonebookEntry.objects.get(code='2622')

        update_response = self.client.post(
            reverse('directory_update', args=[created.pk]),
            data={
                'department': 'Надвірнянський відділ',
                'code': '2622',
                'email': 'nadv@example.com',
                'chief_name': 'Оновлений Керівник',
                'chief_position': 'Начальник відділу',
                'chief_phone': '099-999-99-99',
                'chief_ip': '3001',
                'deputy_name': '',
                'deputy_phone': '',
                'deputy_ip': '',
            },
        )
        self.assertEqual(update_response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.chief_name, 'Оновлений Керівник')

        delete_response = self.client.post(reverse('directory_delete', args=[created.pk]))
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(PhonebookEntry.objects.filter(pk=created.pk).exists())
