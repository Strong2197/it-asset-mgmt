from django.shortcuts import render, redirect, get_object_or_404
from .models import Asset, Category
from .forms import AssetForm
from django.db.models import Q
import openpyxl
from django.http import HttpResponse
from django.forms.models import model_to_dict  # Для клонування
from django.utils import timezone


def export_assets_xlsx(request):
    # 1. Отримуємо параметри
    search_query = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', 'all')

    # 2. Базовий запит
    assets = Asset.objects.all()

    # 3. Фільтр по категорії
    if category_id and category_id != 'all':
        # Використовуємо category_id (автоматичне поле Django для ForeignKey)
        assets = assets.filter(category_id=category_id)

    # 4. Пошук (Назва, Інвентарний, Баркод, Локація)
    if search_query:
        assets = assets.filter(
            Q(name__icontains=search_query) |
            Q(inventory_number__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(account__icontains=search_query)
        )

    # --- СТВОРЕННЯ EXCEL ---
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="inventory_export.xlsx"'

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Майно'

    # Заголовки (Виправлені під вашу модель)
    headers = ['Баркод', 'Інвентарний №', 'Назва', 'Категорія', 'Розташування', 'Відповідальний', 'Рахунок',
               'Дата придбання']
    worksheet.append(headers)

    # Жирний шрифт для заголовка
    for cell in worksheet[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    # Запис даних
    for asset in assets:
        # Безпечне отримання назви категорії
        cat_name = asset.category.name if asset.category else ''

        # Отримання назви рахунку (наприклад "Рахунок 104") замість просто "104"
        # get_account_display() - це стандартний метод Django для полів з choices
        account_name = asset.get_account_display() if hasattr(asset, 'get_account_display') else asset.account

        worksheet.append([
            asset.barcode,
            asset.inventory_number,
            asset.name,
            cat_name,
            asset.location,
            asset.responsible_person,
            account_name,
            asset.purchase_date,
        ])

    # Автоширина колонок
    for col in worksheet.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        # Обмежимо максимальну ширину, щоб не було гігантських колонок
        if adjusted_width > 50:
            adjusted_width = 50
        worksheet.column_dimensions[column].width = adjusted_width

    workbook.save(response)
    return response

# --- 2. КЛОНУВАННЯ МАЙНА ---
def asset_clone(request, pk):
    original_asset = get_object_or_404(Asset, pk=pk)

    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('asset_list')
    else:
        # Беремо дані з оригінала
        initial_data = model_to_dict(original_asset)

        # Очищаємо унікальні поля (щоб не було помилок)
        initial_data.pop('id', None)
        initial_data.pop('inventory_number', None)  # Треба ввести новий
        initial_data.pop('barcode', None)  # Треба ввести новий

        # Створюємо форму з цими даними
        form = AssetForm(initial=initial_data)

    return render(request, 'inventory/asset_form.html', {
        'form': form,
        'title': f'Створення копії: {original_asset.name}'
    })


# --- 1. Список майна (Цієї функції не вистачало) ---
def asset_list(request):
    # 1. Параметри фільтрації
    search_query = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', 'all')
    show_archived = request.GET.get('archived', 'false')  # 'true' або 'false'

    # 2. Базовий запит: фільтруємо по статусу архіву
    if show_archived == 'true':
        assets = Asset.objects.filter(is_archived=True)
    else:
        assets = Asset.objects.filter(is_archived=False)

    # 3. Фільтр по категорії
    if category_id != 'all':
        assets = assets.filter(category_id=category_id)

    # 4. Пошук (працює і для активних, і для архівних)
    if search_query:
        assets = assets.filter(
            Q(name__icontains=search_query) |
            Q(inventory_number__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(account__icontains=search_query) |
            Q(archive_reason__icontains=search_query)  # Шукаємо і в причині архівування
        )

    categories = Category.objects.all()

    return render(request, 'inventory/asset_list.html', {
        'assets': assets,
        'categories': categories,
        'show_archived': show_archived  # Передаємо статус у шаблон
    })


# --- НОВА ФУНКЦІЯ АРХІВУВАННЯ ---
def asset_archive(request, pk):
    asset = get_object_or_404(Asset, pk=pk)

    if request.method == 'POST':
        reason = request.POST.get('archive_reason')
        date = request.POST.get('archive_date')

        if reason and date:
            asset.is_archived = True
            asset.archive_reason = reason
            asset.archive_date = date
            asset.save()

    return redirect('asset_list')


# --- 2. Створення майна ---
def asset_create(request):
    """Створення нового майна"""
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('asset_list')  # Повертаємось до списку
    else:
        form = AssetForm()

    return render(request, 'inventory/asset_form.html', {'form': form, 'title': 'Додати майно'})


# --- 3. Редагування майна ---
def asset_update(request, pk):
    """Редагування існуючого майна"""
    asset = get_object_or_404(Asset, pk=pk)  # Шукаємо запис по ID (pk)

    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)  # Передаємо існуючий об'єкт у форму
        if form.is_valid():
            form.save()
            return redirect('asset_list')
    else:
        form = AssetForm(instance=asset)  # Заповнюємо форму даними з бази

    return render(request, 'inventory/asset_form.html', {'form': form, 'title': 'Редагувати майно'})