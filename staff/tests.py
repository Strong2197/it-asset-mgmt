import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CareerHistory, Employee, KepCertificate


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class StaffViewsTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = Employee.objects.create(
            full_name='Іван Петренко',
            position='Головний спеціаліст',
            department='Івано-Франківський відділ (2610)',
            phone='050-111-22-33',
            rnokpp='1234567890',
        )
        self.dismissed_employee = Employee.objects.create(
            full_name='Оксана Іванчук',
            position='Провідний спеціаліст',
            department='Калуський відділ (2618)',
            rnokpp='0987654321',
            is_dismissed=True,
        )

    def _staff_payload(self, **overrides):
        data = {
            'full_name': 'Петро Зінич',
            'position': 'Провідний інспектор',
            'department': 'Коломийський відділ (2619)',
            'phone': '067-000-00-00',
            'rnokpp': '1112223334',
            'appointment_date': '2025-02-01',
            'appointment_order_number': '12-к',
            'is_dismissed': False,
            'dismissal_date': '',
            'dismissal_order_number': '',
        }
        data.update(overrides)
        return data

    def test_staff_list_shows_only_active_by_default(self):
        response = self.client.get(reverse('staff_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Іван Петренко')
        self.assertNotContains(response, 'Оксана Іванчук')

    def test_staff_list_show_dismissed_and_search(self):
        response = self.client.get(reverse('staff_list'), {'dismissed': 'true', 'q': 'іванчук'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Оксана Іванчук')
        self.assertNotContains(response, 'Іван Петренко')

    def test_staff_create_and_update_creates_career_history(self):
        create_response = self.client.post(reverse('staff_create'), data=self._staff_payload())
        self.assertEqual(create_response.status_code, 302)

        created = Employee.objects.get(full_name='Петро Зінич')
        self.assertEqual(created.rnokpp, '1112223334')

        update_response = self.client.post(
            reverse('staff_update', args=[created.pk]),
            data=self._staff_payload(position='Начальник відділу'),
        )
        self.assertEqual(update_response.status_code, 302)

        created.refresh_from_db()
        self.assertEqual(created.position, 'Начальник відділу')
        self.assertEqual(CareerHistory.objects.filter(employee=created).count(), 1)

    def test_staff_dismiss_marks_employee_as_dismissed(self):
        response = self.client.post(
            reverse('staff_dismiss', args=[self.employee.pk]),
            data={'dismissal_date': '2025-03-01', 'dismissal_order_number': '77-к'},
        )

        self.assertEqual(response.status_code, 302)
        self.employee.refresh_from_db()
        self.assertTrue(self.employee.is_dismissed)
        self.assertEqual(str(self.employee.dismissal_date), '2025-03-01')

    def test_cert_delete_removes_certificate_and_redirects(self):
        cert = KepCertificate.objects.create(
            employee=self.employee,
            file=SimpleUploadedFile('cert.pem', b'certificate-content', content_type='application/octet-stream'),
            original_name='cert.pem',
        )

        response = self.client.post(reverse('cert_delete', args=[cert.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(KepCertificate.objects.filter(pk=cert.pk).exists())
        self.assertIn(reverse('staff_update', args=[self.employee.pk]), response.url)
