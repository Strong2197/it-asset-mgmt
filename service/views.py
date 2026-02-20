from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Sum, Case, When, Value, IntegerField, Q, Count
from django.core.paginator import Page, EmptyPage, PageNotAnInteger
from .models import ServiceTask, ServiceReport, ServiceTaskItem, CARTRIDGE_CHOICES
from .forms import ServiceTaskForm, ServiceReportForm, ServiceItemFormSet, ServiceItemEditFormSet
from django.core.paginator import Paginator


# --- ДОПОМІЖНІ ФУНКЦІЇ ---

def get_all_departments():
    defaults = ['Бухгалтерія', 'Кадри', 'Івано-Франківський відділ']
    db_depts = list(ServiceTask.objects.values_list('department', flat=True).distinct())
    all_depts = sorted(list(set(defaults + db_depts)))
    return list(filter(None, all_depts))


def get_all_requesters():
    """Отримує список усіх унікальних імен замовників для підказок."""
    return list(ServiceTask.objects.values_list('requester_name', flat=True).distinct().order_by('requester_name'))


# --- API ДЛЯ AJAX: Пошук відділу за ПІБ ---
def get_last_department(request):
    name = request.GET.get('name', '').strip()
    if name:
        # Шукаємо останню заявку від цієї людини
        last_task = ServiceTask.objects.filter(requester_name__iexact=name).order_by('-created_at').first()
        if last_task:
            return JsonResponse({'found': True, 'department': last_task.department})

    return JsonResponse({'found': False})


# --- КЛАС РОЗУМНОЇ ПАГІНАЦІЇ ---
class WeightPaginator:
    def __init__(self, queryset, max_weight=15):
        self.pages = []
        self.count = queryset.count()

        current_page = []
        current_weight = 0

        for task in queryset:
            # Вага = к-ть картриджів (або 1, якщо 0)
            w = task.items_count if hasattr(task, 'items_count') and task.items_count > 0 else 1

            # Якщо додавання перевищить ліміт і сторінка не пуста
            if current_weight + w > max_weight and current_page:
                self.pages.append(current_page)
                current_page = []
                current_weight = 0

            current_page.append(task)
            current_weight += w

        if current_page:
            self.pages.append(current_page)

        self.num_pages = len(self.pages)

    def validate_number(self, number):
        """Перевіряє коректність номера сторінки"""
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (ValueError, TypeError):
            raise PageNotAnInteger('Номер сторінки має бути цілим числом')

        if number < 1:
            raise EmptyPage('Номер сторінки менше 1')

        if number > self.num_pages:
            if number == 1 and self.num_pages == 0:
                pass
            else:
                raise EmptyPage('Сторінка не містить результатів')
        return number

    def page(self, number):
        try:
            number = self.validate_number(number)
        except PageNotAnInteger:
            number = 1
        except EmptyPage:
            number = self.num_pages if int(number) > 1 else 1

        if self.num_pages == 0:
            return Page([], number, self)

        return Page(self.pages[number - 1], number, self)


# --- СПИСОК ЗАЯВОК ---
def service_list(request):
    tasks_queryset = ServiceTask.objects.prefetch_related('items').annotate(
        status_rank=Case(
            When(is_completed=False, date_sent__isnull=True, then=Value(1)),
            When(is_completed=False, date_sent__isnull=False, then=Value(2)),
            When(is_completed=True, then=Value(3)),
            default=Value(4), output_field=IntegerField(),
        )
    ).order_by('status_rank', '-date_received')

    status_filter = request.GET.get('filter', 'active')
    if status_filter == 'active':
        tasks_queryset = tasks_queryset.filter(is_completed=False)
    elif status_filter == 'completed':
        tasks_queryset = tasks_queryset.filter(is_completed=True)

    search_query = request.GET.get('q', '').strip().lower()

    if search_query:
        tasks_list = []
        for task in tasks_queryset:
            items_text = " ".join([f"{i.get_item_name_display()} {i.custom_name or ''}" for i in task.items.all()])
            content = f"{task.department} {task.requester_name} {task.description} {items_text}".lower()
            if search_query in content:
                tasks_list.append(task)
    else:
        tasks_list = list(tasks_queryset)

    # ПАГІНАЦІЯ (15 на сторінку)
    paginator = Paginator(tasks_list, 15)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    return render(request, 'service/service_list.html', {
        'tasks': page_obj,
        'current_filter': status_filter,
        'search_query': search_query,
        'total_count': paginator.count
    })


# --- СТВОРЕННЯ ЗАЯВКИ ---
def service_create(request):
    departments = get_all_departments()
    requesters = get_all_requesters()  # Список імен для підказки

    if request.method == 'POST':
        form = ServiceTaskForm(request.POST)
        formset = ServiceItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            task = form.save()
            formset.instance = task
            formset.save()
            return redirect('service_list')
    else:
        form = ServiceTaskForm()
        formset = ServiceItemFormSet()

    return render(request, 'service/service_form.html', {
        'form': form,
        'formset': formset,
        'departments': departments,
        'requesters': requesters,
        'title': 'Створення комплексної заявки'
    })


# --- РЕДАГУВАННЯ ЗАЯВКИ ---
def service_update(request, pk):
    task = get_object_or_404(ServiceTask, pk=pk)
    departments = get_all_departments()
    requesters = get_all_requesters()
    
    if request.method == 'POST':
        form = ServiceTaskForm(request.POST, instance=task)
        # ТУТ ВИКОРИСТОВУЄМО EditFormSet (extra=0)
        formset = ServiceItemEditFormSet(request.POST, instance=task)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('service_list')
    else:
        form = ServiceTaskForm(instance=task)
        # І ТУТ ТАКОЖ EditFormSet
        formset = ServiceItemEditFormSet(instance=task)
    
    return render(request, 'service/service_form.html', {
        'form': form, 
        'formset': formset, 
        'departments': departments,
        'requesters': requesters,
        'title': 'Редагування заявки'
    })


# --- ІНШІ ФУНКЦІЇ ---
def item_receive(request, pk):
    item = get_object_or_404(ServiceTaskItem, pk=pk)
    try:
        qty_to_receive = int(request.GET.get('qty', item.quantity))
    except ValueError:
        qty_to_receive = item.quantity

    if 0 < qty_to_receive < item.quantity:
        item.quantity -= qty_to_receive
        item.save()
        new_item = ServiceTaskItem.objects.create(
            task=item.task,
            item_name=item.item_name,
            custom_name=item.custom_name,
            quantity=qty_to_receive,
            date_back_from_service=timezone.now().date()
        )
        target_item = new_item
        is_split = True
    else:
        item.date_back_from_service = timezone.now().date()
        item.save()
        target_item = item
        is_split = False

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'new_state': 'stocked',
            'item_id': target_item.pk,
            'is_split': is_split,
            'return_url': f"/service/item/{target_item.pk}/return/"
        })
    return redirect('service_list')


def item_return(request, pk):
    item = get_object_or_404(ServiceTaskItem, pk=pk)
    item.date_returned_to_user = timezone.now().date()
    item.save()

    parent_task = item.task
    all_items_done = not parent_task.items.filter(date_returned_to_user__isnull=True).exists()
    if all_items_done:
        parent_task.is_completed = True
        parent_task.date_returned = timezone.now().date()
        parent_task.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'new_state': 'issued',
            'date_str': item.date_returned_to_user.strftime("%d.%m"),
            'task_completed': all_items_done,
            'task_id': parent_task.pk
        })
    return redirect('service_list')


def service_receive_from_repair(request, pk):
    return redirect('service_list')


def service_quick_return(request, pk):
    return redirect('service_list')


def print_preview(request):
    tasks_to_print = ServiceTask.objects.filter(
        date_sent__isnull=True, is_completed=False
    ).prefetch_related('items').order_by('department')
    total_qty = ServiceTaskItem.objects.filter(task__in=tasks_to_print).aggregate(total=Sum('quantity'))['total'] or 0
    return render(request, 'service/print_preview.html', {'tasks': tasks_to_print, 'total_cartridges': total_qty})


def save_report(request):
    if request.method == 'POST':
        tasks_to_save = ServiceTask.objects.filter(date_sent__isnull=True, is_completed=False)
        if not tasks_to_save.exists(): return redirect('service_list')
        report = ServiceReport.objects.create()
        report.tasks.set(tasks_to_save)
        tasks_to_save.update(date_sent=timezone.now().date())
        return redirect('report_detail', pk=report.pk)
    return redirect('service_list')


def report_list(request):
    reports = ServiceReport.objects.annotate(total_items=Sum('tasks__items__quantity')).order_by('-created_at')
    return render(request, 'service/report_list.html', {'reports': reports})


def report_detail(request, pk):
    report = get_object_or_404(ServiceReport, pk=pk)
    items = ServiceTaskItem.objects.filter(task__in=report.tasks.all())
    stats = {}
    sort_map = {key: index for index, (key, label) in enumerate(CARTRIDGE_CHOICES)}

    for item in items:
        if item.item_name == 'Інше':
            name = item.custom_name if item.custom_name else 'Інше (без назви)'
        else:
            name = item.get_item_name_display()

        qty = item.quantity
        dept = item.task.department or "Не вказано"
        sort_index = sort_map.get(item.item_name, 999)

        if name not in stats: stats[name] = {'total_qty': 0, 'departments': {}, 'notes': [], 'sort_index': sort_index}
        stats[name]['total_qty'] += qty

        if dept not in stats[name]['departments']: stats[name]['departments'][dept] = {'items': [], 'sum_qty': 0}
        stats[name]['departments'][dept]['items'].append(item)
        stats[name]['departments'][dept]['sum_qty'] += qty

        if item.item_name == 'Інше':
            desc = item.task.description
            if desc and desc not in stats[name]['notes']: stats[name]['notes'].append(desc)

    sorted_stats = dict(sorted(stats.items(), key=lambda item: (item[1]['sort_index'], item[0])))
    grand_total = sum(data['total_qty'] for data in sorted_stats.values())
    return render(request, 'service/report_detail.html',
                  {'report': report, 'stats': sorted_stats, 'grand_total': grand_total})


def report_edit(request, pk):
    report = get_object_or_404(ServiceReport, pk=pk)
    if request.method == 'POST':
        old_tasks = list(report.tasks.all())
        form = ServiceReportForm(request.POST, instance=report)
        if form.is_valid():
            saved_report = form.save()
            new_tasks = saved_report.tasks.all()
            for task in old_tasks:
                if task not in new_tasks:
                    task.date_sent = None
                    task.save()
            for task in new_tasks:
                if not task.date_sent:
                    task.date_sent = saved_report.created_at.date()
                    task.save()
            return redirect('report_detail', pk=report.pk)
    else:
        form = ServiceReportForm(instance=report)
    return render(request, 'service/report_form.html', {'form': form, 'title': f'Редагування акту №{report.id}'})
