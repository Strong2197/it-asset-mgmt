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
