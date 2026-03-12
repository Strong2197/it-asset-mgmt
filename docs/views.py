from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Document
from .forms import DocumentForm

class DocumentListView(ListView):
    model = Document
    template_name = 'docs/doc_list.html'
    context_object_name = 'documents'
    
    def get_queryset(self):
        # Віддаємо всі записи, відсортовані за датою (нові зверху)
        return Document.objects.all().order_by('-created_at')


class DocumentCreateView(CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'docs/doc_form.html'
    success_url = reverse_lazy('doc_list')

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