from django.shortcuts import render, redirect, get_object_or_404
from .models import Document
from .forms import DocumentForm
from config.view_helpers import save_model_form, delete_on_post


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
    return save_model_form(
        request,
        form_class=DocumentForm,
        template_name='docs/doc_form.html',
        success_url='doc_list',
        title='Додати посилання',
    )


def doc_update(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    return save_model_form(
        request,
        form_class=DocumentForm,
        template_name='docs/doc_form.html',
        success_url='doc_list',
        instance=doc,
        title='Редагувати посилання',
    )


def doc_delete(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    return delete_on_post(request, obj=doc, success_url='doc_list')
