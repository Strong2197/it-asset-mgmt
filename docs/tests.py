from django.test import TestCase
from django.urls import reverse

from .models import Document


class DocsViewsTests(TestCase):
    def setUp(self):
        self.doc1 = Document.objects.create(
            title='Інструкція з налаштування принтера',
            doc_type='instruction',
            google_drive_link='https://example.com/instruction',
            description='Покроковий опис для нових співробітників',
        )
        self.doc2 = Document.objects.create(
            title='Драйвер сканера',
            doc_type='driver',
            google_drive_link='https://example.com/driver',
            description='Остання стабільна версія',
        )

    def test_doc_list_renders_documents(self):
        response = self.client.get(reverse('doc_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Інструкція з налаштування принтера')
        self.assertContains(response, 'Драйвер сканера')

    def test_doc_create_update_delete(self):
        create_response = self.client.post(
            reverse('doc_create'),
            data={
                'title': 'Шаблон наказу',
                'doc_type': 'template',
                'google_drive_link': 'https://example.com/template',
                'description': 'Стандартний шаблон наказу',
            },
        )
        self.assertEqual(create_response.status_code, 302)
        created = Document.objects.get(title='Шаблон наказу')

        update_response = self.client.post(
            reverse('doc_update', args=[created.pk]),
            data={
                'title': 'Шаблон наказу (оновлено)',
                'doc_type': 'template',
                'google_drive_link': 'https://example.com/template-v2',
                'description': 'Оновлений шаблон',
            },
        )
        self.assertEqual(update_response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.title, 'Шаблон наказу (оновлено)')

        delete_response = self.client.post(reverse('doc_delete', args=[created.pk]))
        self.assertEqual(delete_response.status_code, 302)
        self.assertFalse(Document.objects.filter(pk=created.pk).exists())