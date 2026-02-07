from django.shortcuts import render, redirect, get_object_or_404
from .models import Document
from .forms import DocumentForm
from django.db.models import Q


def doc_list(request):
    query = request.GET.get('q', '')

    # Сортування по created_at (як у вашій моделі)
    documents = Document.objects.all().order_by('-created_at')

    # Пошук
    if query:
        documents = documents.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, 'docs/doc_list.html', {
        'documents': documents,
        'query': query
    })


def doc_create(request):
    if request.method == 'POST':
        # Прибрали request.FILES
        form = DocumentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('doc_list')
    else:
        form = DocumentForm()
    return render(request, 'docs/doc_form.html', {'form': form, 'title': 'Додати посилання'})


def doc_update(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    if request.method == 'POST':
        # Прибрали request.FILES
        form = DocumentForm(request.POST, instance=doc)
        if form.is_valid():
            form.save()
            return redirect('doc_list')
    else:
        form = DocumentForm(instance=doc)
    return render(request, 'docs/doc_form.html', {'form': form, 'title': 'Редагувати посилання'})


def doc_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk)

    if request.method == 'POST':
        doc.delete()
        return redirect('doc_list')

    # Якщо хтось спробує відкрити посилання в браузері напряму - просто перекидаємо назад
    return redirect('doc_list')