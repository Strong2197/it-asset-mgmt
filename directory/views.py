from django.shortcuts import render, redirect, get_object_or_404
from .models import PhonebookEntry
from .forms import PhonebookForm
from django.db.models import Q
from django.db.models.functions import Lower
from django.core.paginator import Paginator

def directory_list(request):
    query = request.GET.get('q', '').strip().lower()  # Перетворюємо пошуковий запит у нижній регістр
    entries = PhonebookEntry.objects.all()

    if query:
        # Використовуємо Lower() для кожного поля, щоб ігнорувати регістр
        entries = entries.annotate(
            dept_lower=Lower('department'),
            code_lower=Lower('code'),
            chief_lower=Lower('chief_name'),
            deputy_lower=Lower('deputy_name')
        ).filter(
            Q(dept_lower__contains=query) |
            Q(code_lower__contains=query) |
            Q(chief_lower__contains=query) |
            Q(deputy_lower__contains=query)
        )

    # Логіка для AJAX (живого пошуку)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'directory/directory_rows.html', {'entries': entries})

    # Пагінація
    paginator = Paginator(entries, 30)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    return render(request, 'directory/directory_list.html', {
        'entries': page_obj,
        'query': query
    })

# ... інші функції (create, update, delete) залишаються без змін ...
def directory_create(request):
    if request.method == 'POST':
        form = PhonebookForm(request.POST)
        if form.is_valid(): form.save(); return redirect('directory_list')
    else: form = PhonebookForm()
    return render(request, 'directory/directory_form.html', {'form': form, 'title': 'Додати відділ'})

def directory_update(request, pk):
    entry = get_object_or_404(PhonebookEntry, pk=pk)
    if request.method == 'POST':
        form = PhonebookForm(request.POST, instance=entry)
        if form.is_valid(): form.save(); return redirect('directory_list')
    else: form = PhonebookForm(instance=entry)
    return render(request, 'directory/directory_form.html', {'form': form, 'title': 'Редагувати відділ'})

def directory_delete(request, pk):
    entry = get_object_or_404(PhonebookEntry, pk=pk)
    if request.method == 'POST': entry.delete()
    return redirect('directory_list')