from django.shortcuts import render, redirect, get_object_or_404
from .models import Asset, Category
from .forms import AssetForm
from django.db.models import Q
import openpyxl
from django.http import HttpResponse
from django.forms.models import model_to_dict  # Для клонування
from django.utils import timezone
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter # <--- ЦЕЙ ІМПОРТ ПОТРІБЕН ДЛЯ ФІЛЬТРУ
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def export_assets_xlsx(request):
    # 1. Параметри та фільтрація
    search_query = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', 'all')
    show_archived = request.GET.get('archived', 'false')

    if show_archived == 'true':
        assets = Asset.objects.filter(is_archived=True)
    else:
        assets = Asset.objects.filter(is_archived=False)

    if category_id and category_id != 'all':
        assets = assets.filter(category_id=category_id)

    if search_query:
        assets = assets.filter(
            Q(name__icontains=search_query) |
            Q(inventory_number__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(account__icontains=search_query) |
            Q(archive_reason__icontains=search_query)
        )

    # --- СТВОРЕННЯ EXCEL ---
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="inventory_export.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Майно'

    # --- СТИЛІ ---
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'),
                         bottom=Side(style='thin'))
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell_align_center = Alignment(horizontal="center", vertical="center")
    cell_align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # --- ЗАГОЛОВКИ ---
    headers = ['Баркод', 'Інвентарний №', 'Назва', 'Категорія', 'Розташування', 'Відповідальний', 'Рахунок',
               'Дата придбання']
    if show_archived == 'true':
        headers.extend(['Причина архівування', 'Дата архівування'])

    ws.append(headers)

    # === ВКЛЮЧАЄМО ФІЛЬТР ===
    # Визначаємо букву останньої колонки (наприклад, "H" або "J")
    last_col_letter = get_column_letter(len(headers))
    # Встановлюємо фільтр на перший рядок від A1 до останньої колонки
    ws.auto_filter.ref = f"A1:{last_col_letter}1"
    # ========================

    # Застосовуємо стиль до заголовка
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # --- ДАНІ ---
    for asset in assets:
        cat_name = asset.category.name if asset.category else ''
        account_name = asset.get_account_display() if hasattr(asset, 'get_account_display') else asset.account

        row_data = [
            asset.barcode,
            asset.inventory_number,
            asset.name,
            cat_name,
            asset.location,
            asset.responsible_person,
            account_name,
            asset.purchase_date,
        ]

        if show_archived == 'true':
            row_data.extend([asset.archive_reason, asset.archive_date])

        ws.append(row_data)

        # Стилізація рядка даних
        current_row = ws[ws.max_row]
        for cell in current_row:
            cell.border = thin_border
            if cell.column == 3:  # Колонка "Назва"
                cell.alignment = cell_align_left
            else:
                cell.alignment = cell_align_center

    # --- АВТОШИРИНА ---
    ws.column_dimensions['C'].width = 50
    for col in ws.columns:
        column_letter = col[0].column_letter
        if column_letter == 'C': continue

        max_length = 0
        for cell in col:
            try:
                if len(str(cell.value)) > max_length: max_length = len(str(cell.value))
            except:
                pass

        adjusted_width = (max_length + 4)
        if adjusted_width < 10: adjusted_width = 10
        if adjusted_width > 30: adjusted_width = 30

        ws.column_dimensions[column_letter].width = adjusted_width

    wb.save(response)
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
    # 1. Отримання параметрів
    search_query = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', 'all')
    show_archived = request.GET.get('archived', 'false')

    # 2. Базовий запит
    if show_archived == 'true':
        assets = Asset.objects.filter(is_archived=True)
    else:
        assets = Asset.objects.filter(is_archived=False)

    # 3. Фільтрація
    if category_id != 'all':
        assets = assets.filter(category_id=category_id)

    if search_query:
        assets = assets.filter(
            Q(name__icontains=search_query) |
            Q(inventory_number__icontains=search_query) |
            Q(barcode__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(account__icontains=search_query) |
            Q(archive_reason__icontains=search_query)
        )

    # 4. ПАГІНАЦІЯ (30 елементів)
    paginator = Paginator(assets, 30)
    page = request.GET.get('page')

    try:
        assets_page = paginator.page(page)
    except PageNotAnInteger:
        assets_page = paginator.page(1)
    except EmptyPage:
        assets_page = paginator.page(paginator.num_pages)

    categories = Category.objects.all()

    return render(request, 'inventory/asset_list.html', {
        'assets': assets_page,
        'categories': categories,
        'show_archived': show_archived,
        'search_query': search_query,
        'current_category': category_id,
        'total_count': paginator.count
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