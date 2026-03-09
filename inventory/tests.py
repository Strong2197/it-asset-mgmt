from django.test import TestCase
from django.urls import reverse

from .models import Asset, Category


class InventoryViewsTests(TestCase):
    def setUp(self):
        self.category_pc = Category.objects.create(name='ПК')
        self.category_monitor = Category.objects.create(name='Монітор')

        self.asset_active = Asset.objects.create(
            name='Робоча станція Dell OptiPlex',
            category=self.category_pc,
            inventory_number='INV-001',
            barcode='BC-001',
            responsible_person='Костишин О.В.',
            location='100',
            account='104',
            notes='Основне робоче місце',
        )
        self.asset_archived = Asset.objects.create(
            name='Монітор Samsung',
            category=self.category_monitor,
            inventory_number='INV-002',
            barcode='BC-002',
            responsible_person='Олійник М.Р.',
            location='504',
            account='113',
            is_archived=True,
            archive_reason='Списання',
            archive_date='2025-01-10',
        )

    def _asset_payload(self, **overrides):
        data = {
            'name': 'Ноутбук Lenovo',
            'category': self.category_pc.pk,
            'inventory_number': 'INV-010',
            'barcode': 'BC-010',
            'responsible_person': 'Костишин О.В.',
            'location': '100',
            'account': '104',
            'purchase_date': '2025-02-01',
            'notes': 'Тестовий запис',
        }
        data.update(overrides)
        return data

    def test_asset_list_filters_only_active_by_default(self):
        response = self.client.get(reverse('asset_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Робоча станція Dell OptiPlex')
        self.assertNotContains(response, 'Монітор Samsung')

    def test_asset_list_search_finds_by_name_case_insensitive(self):
        response = self.client.get(reverse('asset_list'), {'search': 'dell'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Робоча станція Dell OptiPlex')
        self.assertNotContains(response, 'Монітор Samsung')

    def test_asset_create_update_archive(self):
        create_response = self.client.post(reverse('asset_create'), data=self._asset_payload())
        self.assertEqual(create_response.status_code, 302)

        created = Asset.objects.get(inventory_number='INV-010')

        update_response = self.client.post(
            reverse('asset_update', args=[created.pk]),
            data=self._asset_payload(name='Ноутбук Lenovo (оновлено)', barcode='BC-010-U'),
        )
        self.assertEqual(update_response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.name, 'Ноутбук Lenovo (оновлено)')
        self.assertEqual(created.barcode, 'BC-010-U')

        archive_response = self.client.post(
            reverse('asset_archive', args=[created.pk]),
            data={'archive_reason': 'Передано в сервіс', 'archive_date': '2025-03-01'},
        )
        self.assertEqual(archive_response.status_code, 302)
        created.refresh_from_db()
        self.assertTrue(created.is_archived)
        self.assertEqual(created.archive_reason, 'Передано в сервіс')

    def test_asset_clone_get_prepopulates_and_clears_unique_fields(self):
        response = self.client.get(reverse('asset_clone', args=[self.asset_active.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Робоча станція Dell OptiPlex')
        self.assertNotContains(response, 'value="INV-001"', html=False)
        self.assertNotContains(response, 'value="BC-001"', html=False)

    def test_export_assets_xlsx_returns_excel_file(self):
        response = self.client.get(reverse('export_assets_xlsx'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn('attachment; filename="inventory_export.xlsx"', response['Content-Disposition'])
        self.assertGreater(len(response.content), 0)
