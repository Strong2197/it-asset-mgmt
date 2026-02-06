from django.shortcuts import render, redirect, get_object_or_404
from .models import Document
from .forms import DocumentForm
from django.db.models import Q


def doc_list(request):
    query = request.GET.get('q', '')
    doc_type = request.GET.get('type', '')  # Фільтр по типу (драйвер/інструкція)

    documents = Document.objects.all().order_by('-created_at')

    if query:
        documents = documents.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    if doc_type:
        documents = documents.filter(doc_type=doc_type)

    return render(request, 'docs/doc_list.html', {
        'documents': documents,
        'query': query,
        'selected_type': doc_type
    })


def doc_create(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('doc_list')
    else:
        form = DocumentForm()
    return render(request, 'docs/doc_form.html', {'form': form, 'title': 'Додати файл'})


def doc_update(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        form = DocumentForm(request.POST, instance=doc)
        if form.is_valid():
            form.save()
            return redirect('doc_list')
    else:
        form = DocumentForm(instance=doc)
    return render(request, 'docs/doc_form.html', {'form': form, 'title': 'Редагувати файл'})