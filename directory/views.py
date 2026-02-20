from django.shortcuts import render, redirect, get_object_or_404
from .models import PhonebookEntry
from .forms import PhonebookForm
from django.db.models import Q
from django.core.paginator import Paginator

def directory_list(request):
    query = request.GET.get('q', '')
    entries = PhonebookEntry.objects.all()

    if query:
        entries = entries.filter(
            Q(department__icontains=query) |
            Q(code__icontains=query) |
            Q(chief_name__icontains=query) |
            Q(chief_phone__icontains=query) |
            Q(deputy_name__icontains=query) |
            Q(deputy_phone__icontains=query)
        )

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