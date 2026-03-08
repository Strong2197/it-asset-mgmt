from django.shortcuts import render, redirect, get_object_or_404
from .models import PhonebookEntry
from .forms import PhonebookForm
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string


def directory_list(request):
    query = request.GET.get('q', '').strip()

    entries = PhonebookEntry.objects.all()

    if query:
        entries = entries.filter(
            Q(department__icontains=query)
            | Q(code__icontains=query)
            | Q(chief_name__icontains=query)
            | Q(chief_phone__icontains=query)
            | Q(deputy_name__icontains=query)
            | Q(deputy_phone__icontains=query)
            | Q(email__icontains=query)
        )

        # SQLite може некоректно порівнювати регістр для кирилиці в icontains,
        # тому робимо fallback на Python casefold.
        if not entries.exists():
            query_cf = query.casefold()
            matched_ids = [
                item.pk
                for item in PhonebookEntry.objects.all()
            entries = [
                item for item in PhonebookEntry.objects.all()
                if query_cf in (
                    f"{item.department} {item.code} {item.chief_name} "
                    f"{item.chief_phone} {item.deputy_name} {item.deputy_phone} {item.email}"
                ).casefold()
            ]
            entries = PhonebookEntry.objects.filter(pk__in=matched_ids)

    total_count = entries.count()

    # Логіка для AJAX (живого пошуку).
    # Додаємо підтримку query-прапорця, бо деякі проксі можуть зрізати X-Requested-With.
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    if is_ajax:

    total_count = len(entries) if isinstance(entries, list) else entries.count()

    # Логіка для AJAX (живого пошуку).
    # Додаємо підтримку query-прапорця, бо деякі проксі можуть зрізати X-Requested-With.
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    if is_ajax:
    total_count = entries.count()

    # Логіка для AJAX (живого пошуку)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        rows_html = render_to_string('directory/directory_rows.html', {'entries': entries}, request=request)
        return JsonResponse({'rows_html': rows_html, 'total_count': total_count})

    return render(request, 'directory/directory_list.html', {
        'entries': entries,
        'query': query,
        'total_count': total_count,
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
