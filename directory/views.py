from django.shortcuts import render, redirect, get_object_or_404
from .models import PhonebookEntry
from .forms import PhonebookForm
from django.db.models import Q


def directory_list(request):
    query = request.GET.get('q', '').strip().lower()  # Перетворюємо запит у нижній регістр

    # Отримуємо всі записи (воно відсортується по коду, як ми писали раніше)
    all_entries = PhonebookEntry.objects.all()

    if query:
        # Фільтруємо список вручну засобами Python
        filtered_entries = []
        for item in all_entries:
            # Збираємо всі текстові поля в один рядок для пошуку
            search_content = f"{item.department} {item.code} {item.chief_name} {item.chief_phone} {item.deputy_name} {item.deputy_phone}".lower()

            if query in search_content:
                filtered_entries.append(item)

        entries = filtered_entries
    else:
        entries = all_entries

    # Логіка для AJAX (живого пошуку)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'directory/directory_rows.html', {'entries': entries})

    return render(request, 'directory/directory_list.html', {
        'entries': entries,
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