from django.shortcuts import render, redirect, get_object_or_404
from .models import Document
from .forms import DocumentForm


def doc_list(request):
    # Отримуємо запит і переводимо його в нижній регістр для порівняння
    query = request.GET.get('q', '').strip().lower()

    # Сортування по created_at (нові зверху)
    all_documents = Document.objects.all().order_by('-created_at')

    if query:
        # Фільтруємо список засобами Python, щоб уникнути проблем SQLite з регістром кирилиці
        filtered_docs = []
        for doc in all_documents:
            # Збираємо заголовок та опис, переводимо в нижній регістр
            title = (doc.title or "").lower()
            description = (doc.description or "").lower()

            if query in title or query in description:
                filtered_docs.append(doc)

        documents = filtered_docs
    else:
        documents = all_documents

    return render(request, 'docs/doc_list.html', {
        'documents': documents,
        'query': query
    })


# Решта функцій (create, update, delete) залишаються без змін
def doc_create(request):
    if request.method == 'POST':
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
    return redirect('doc_list')