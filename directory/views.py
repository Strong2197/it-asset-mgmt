from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q

from .models import PhonebookEntry
from .forms import PhonebookForm
from config.search_helpers import filter_by_text_query


class DirectoryListView(ListView):
    model = PhonebookEntry
    template_name = 'directory/directory_list.html'
    context_object_name = 'entries'

    def get_queryset(self):
        # Базовий запит
        queryset = PhonebookEntry.objects.all()
        query = self.request.GET.get('q', '').strip()

        if query:
            # Спроба пошуку через БД
            queryset = queryset.filter(
                Q(department__icontains=query) | Q(code__icontains=query) |
                Q(chief_name__icontains=query) | Q(chief_phone__icontains=query) |
                Q(deputy_name__icontains=query) | Q(deputy_phone__icontains=query) |
                Q(email__icontains=query)
            )

            # Fallback для кирилиці через Python (як у вашому старому коді)
            if not queryset.exists():
                matched_items = filter_by_text_query(
                    PhonebookEntry.objects.all(), query,
                    lambda item: f"{item.department} {item.code} {item.chief_name} {item.chief_phone} {item.deputy_name} {item.deputy_phone} {item.email}"
                )
                queryset = PhonebookEntry.objects.filter(pk__in=[item.pk for item in matched_items])
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['total_count'] = self.get_queryset().count()
        return context

    def render_to_response(self, context, **response_kwargs):
        # Логіка для AJAX (живого пошуку)
        is_ajax = self.request.headers.get('x-requested-with') == 'XMLHttpRequest' or self.request.GET.get('ajax') == '1'
        if is_ajax:
            rows_html = render_to_string('directory/directory_rows.html', {'entries': context['entries']}, request=self.request)
            return JsonResponse({'rows_html': rows_html, 'total_count': context['total_count']})
        
        return super().render_to_response(context, **response_kwargs)


class DirectoryCreateView(CreateView):
    model = PhonebookEntry
    form_class = PhonebookForm
    template_name = 'directory/directory_form.html'
    success_url = reverse_lazy('directory_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Додати відділ'
        return context


class DirectoryUpdateView(UpdateView):
    model = PhonebookEntry
    form_class = PhonebookForm
    template_name = 'directory/directory_form.html'
    success_url = reverse_lazy('directory_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редагувати відділ'
        return context


class DirectoryDeleteView(DeleteView):
    model = PhonebookEntry
    success_url = reverse_lazy('directory_list')