from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from .models import Document
from .forms import DocumentForm
from django.views.generic import CreateView, UpdateView, DeleteView
from config.search_helpers import filter_by_text_query


def doc_list(request):
    # Отримуємо запит і переводимо його в нижній регістр для порівняння
    query = request.GET.get('q', '').strip()

    # Сортування по created_at (нові зверху)
    all_documents = Document.objects.all().order_by('-created_at')

    if query:
        # Фільтруємо список засобами Python, щоб уникнути проблем SQLite з регістром кирилиці
        documents = filter_by_text_query(
            all_documents,
            query,
            lambda doc: f"{doc.title or ''} {doc.description or ''}",
        )
    else:
        documents = all_documents

    return render(request, 'docs/doc_list.html', {
        'documents': documents,
        'query': query
    })


class DocumentCreateView(CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'docs/doc_form.html'
    success_url = reverse_lazy('doc_list')

    # Передаємо додатковий контекст (заголовок), як ви це робили у своєму хелпері
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Додати посилання'
        return context

class DocumentUpdateView(UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'docs/doc_form.html'
    success_url = reverse_lazy('doc_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редагувати посилання'
        return context

class DocumentDeleteView(DeleteView):
    model = Document
    success_url = reverse_lazy('doc_list')
    # DeleteView очікує POST-запит для видалення, що ідеально збігається з вашим підходом