from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField 
from .models import ServiceTask, ServiceReport, ServiceTaskItem, CARTRIDGE_CHOICES
from .forms import ServiceTaskForm, ServiceReportForm, ServiceItemFormSet
from django.http import JsonResponse
from django.db.models import Sum


# --- ДОПОМІЖНА ФУНКЦІЯ ---
def get_all_departments():
    defaults = ['Бухгалтерія', 'Кадри', 'Івано-Франківський відділ']
    db_depts = list(ServiceTask.objects.values_list('department', flat=True).distinct())
    all_depts = sorted(list(set(defaults + db_depts)))
    return list(filter(None, all_depts))


# --- СПИСОК ЗАЯВОК ---
def service_list(request):
    tasks = ServiceTask.objects.prefetch_related('items').annotate(
        # Створюємо віртуальне поле 'status_rank' для сортування
        status_rank=Case(
            # 1. Пріоритет: Нові (чекають відправки)
            When(is_completed=False, date_sent__isnull=True, then=Value(1)),

            # 2. Пріоритет: В роботі (відправлені, але не закриті)
            When(is_completed=False, date_sent__isnull=False, then=Value(2)),

            # 3. Пріоритет: Виконані (Архів)
            When(is_completed=True, then=Value(3)),
            
            default=Value(4), # На всяк випадок
            output_field=IntegerField(),
        )
    ).order_by('status_rank', '-date_received') # Спочатку по статусу, потім новіші за датою

    return render(request, 'service/service_list.html', {'tasks': tasks})


# --- СТВОРЕННЯ ЗАЯВКИ ---
def service_create(request):
    departments = get_all_departments()

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
        'title': 'Створення комплексної заявки'
    })


# --- РЕДАГУВАННЯ ЗАЯВКИ ---
def service_update(request, pk):
    task = get_object_or_404(ServiceTask, pk=pk)
    departments = get_all_departments()  # Додаємо відділи сюди теж

    if request.method == 'POST':
        form = ServiceTaskForm(request.POST, instance=task)
        formset = ServiceItemFormSet(request.POST, instance=task)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('service_list')
    else:
        form = ServiceTaskForm(instance=task)
        formset = ServiceItemFormSet(instance=task)

    return render(request, 'service/service_form.html', {
        'form': form,
        'formset': formset,
        'departments': departments,  # Передаємо в шаблон
        'title': 'Редагування заявки'
    })


# --- НОВІ ФУНКЦІЇ ДЛЯ КАРТРИДЖІВ (ITEMS) ---

def item_receive(request, pk):
    item = get_object_or_404(ServiceTaskItem, pk=pk)
    
    # Виконуємо дію
    item.date_back_from_service = timezone.now().date()
    item.save()

    # Якщо це AJAX запит (від нашого JavaScript)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'new_state': 'stocked', # Стан: на складі
            'item_id': item.pk,
            'return_url': f"/service/item/{item.pk}/return/" # URL для наступної кнопки
        })

    return redirect('service_list')


def item_return(request, pk):
    item = get_object_or_404(ServiceTaskItem, pk=pk)
    
    # Виконуємо дію
    item.date_returned_to_user = timezone.now().date()
    item.save()

    # Перевіряємо батьківську заявку
    parent_task = item.task
    all_items_done = not parent_task.items.filter(date_returned_to_user__isnull=True).exists()
    
    if all_items_done:
        parent_task.is_completed = True
        parent_task.date_returned = timezone.now().date()
        parent_task.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'new_state': 'issued', # Стан: видано
            'date_str': item.date_returned_to_user.strftime("%d.%m"),
            'task_completed': all_items_done, # Чи закрилась вся заявка
            'task_id': parent_task.pk
        })

    return redirect('service_list')


# --- СТАРІ ФУНКЦІЇ (МОЖНА ЗАЛИШИТИ ДЛЯ СУМІСНОСТІ АБО ВИДАЛИТИ) ---
# Вони вже не використовуються в новому інтерфейсі, але хай будуть про всяк випадок

def service_receive_from_repair(request, pk):
    task = get_object_or_404(ServiceTask, pk=pk)
    task.date_back_from_service = timezone.now().date()
    task.save()
    return redirect('service_list')


def service_quick_return(request, pk):
    task = get_object_or_404(ServiceTask, pk=pk)
    task.date_returned = timezone.now().date()
    task.is_completed = True
    task.save()
    return redirect('service_list')


# --- РОБОТА ЗІ ЗВІТАМИ (АКТАМИ) ---

def print_preview(request):
    tasks_to_print = ServiceTask.objects.filter(
        date_sent__isnull=True,
        is_completed=False
    ).prefetch_related('items').order_by('department')

    # Рахуємо загальну кількість картриджів (сума поля quantity у items)
    # Ми беремо всі items, які належать відфільтрованим заявкам (tasks_to_print)
    total_qty = ServiceTaskItem.objects.filter(task__in=tasks_to_print).aggregate(total=Sum('quantity'))['total'] or 0

    return render(request, 'service/print_preview.html', {
        'tasks': tasks_to_print,
        'total_cartridges': total_qty  # Передаємо нову змінну в шаблон
    })
def save_report(request):
    if request.method == 'POST':
        tasks_to_save = ServiceTask.objects.filter(date_sent__isnull=True, is_completed=False)
        if not tasks_to_save.exists():
            return redirect('service_list')

        report = ServiceReport.objects.create()
        report.tasks.set(tasks_to_save)
        tasks_to_save.update(date_sent=timezone.now().date())
        return redirect('report_detail', pk=report.pk)

    return redirect('service_list')


def report_list(request):
    # Використовуємо annotate, щоб база даних сама порахувала суму для кожного звіту
    reports = ServiceReport.objects.annotate(
        total_items=Sum('tasks__items__quantity')
    ).order_by('-created_at')

    return render(request, 'service/report_list.html', {'reports': reports})


# service/views.py

# service/views.py

def report_detail(request, pk):
    report = get_object_or_404(ServiceReport, pk=pk)

    items = ServiceTaskItem.objects.filter(task__in=report.tasks.all())
    stats = {}

    sort_map = {key: index for index, (key, label) in enumerate(CARTRIDGE_CHOICES)}

    for item in items:
        # Назва
        if item.item_name == 'Інше':
            name = item.custom_name if item.custom_name else 'Інше (без назви)'
        else:
            name = item.get_item_name_display()

        qty = item.quantity
        dept = item.task.department or "Не вказано"
        sort_index = sort_map.get(item.item_name, 999)

        # 1. Створюємо запис для картриджа, якщо немає
        if name not in stats:
            stats[name] = {
                'total_qty': 0,
                'departments': {},
                'notes': [],
                'sort_index': sort_index
            }

        stats[name]['total_qty'] += qty

        # 2. Створюємо запис для відділу, якщо немає
        if dept not in stats[name]['departments']:
            # ТУТ ЗМІНА: зберігаємо і список об'єктів, і суму штук
            stats[name]['departments'][dept] = {
                'items': [],
                'sum_qty': 0
            }

        # 3. Наповнюємо даними
        stats[name]['departments'][dept]['items'].append(item)
        stats[name]['departments'][dept]['sum_qty'] += qty  # Додаємо реальну кількість

        # Примітки
        if item.item_name == 'Інше':
            desc = item.task.description
            if desc and desc not in stats[name]['notes']:
                stats[name]['notes'].append(desc)

    # Сортування
    sorted_stats = dict(sorted(stats.items(), key=lambda item: (item[1]['sort_index'], item[0])))

    grand_total = sum(data['total_qty'] for data in sorted_stats.values())

    return render(request, 'service/report_detail.html', {
        'report': report,
        'stats': sorted_stats,
        'grand_total': grand_total
    })


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

    return render(request, 'service/report_form.html', {
        'form': form,
        'title': f'Редагування акту №{report.id}'
    })
