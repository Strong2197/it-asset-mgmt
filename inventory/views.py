from django.shortcuts import render, redirect, get_object_or_404
from .models import Asset, Category
from .forms import AssetForm
from django.db.models import Q


# --- 1. Список майна (Цієї функції не вистачало) ---
def asset_list(request):
    query = request.GET.get('q', '')  # Отримуємо пошуковий запит
    assets = Asset.objects.all()
    categories = Category.objects.all()

    if query:
        assets = assets.filter(
            Q(name__icontains=query) |
            Q(inventory_number__icontains=query) |
            Q(barcode__icontains=query) |
            Q(responsible_person__icontains=query)
        )

    return render(request, 'inventory/asset_list.html', {
        'assets': assets,
        'categories': categories  # <--- Додали це
    })


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