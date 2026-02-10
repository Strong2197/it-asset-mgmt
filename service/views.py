from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField 
from .models import ServiceTask, ServiceReport, ServiceTaskItem
from .forms import ServiceTaskForm, ServiceReportForm, ServiceItemFormSet


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
    item.date_back_from_service = timezone.now().date()
    item.save()
    return redirect('service_list')


def item_return(request, pk):
    item = get_object_or_404(ServiceTaskItem, pk=pk)
    item.date_returned_to_user = timezone.now().date()
    item.save()

    # Автоматичне закриття заявки, якщо всі картриджі видані
    parent_task = item.task
    if not parent_task.items.filter(date_returned_to_user__isnull=True).exists():
        parent_task.is_completed = True
        parent_task.date_returned = timezone.now().date()
        parent_task.save()

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
    # Додаємо .prefetch_related('items'), щоб бачити картриджі
    tasks_to_print = ServiceTask.objects.filter(
        date_sent__isnull=True,
        is_completed=False
    ).prefetch_related('items').order_by('department')  # Сортуємо по відділу для зручності

    return render(request, 'service/print_preview.html', {'tasks': tasks_to_print})

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
    reports = ServiceReport.objects.all().order_by('-created_at')
    return render(request, 'service/report_list.html', {'reports': reports})


def report_detail(request, pk):
    report = get_object_or_404(ServiceReport, pk=pk)

    # 1. Знаходимо всі items
    items = ServiceTaskItem.objects.filter(task__in=report.tasks.all())
    stats = {}

    for item in items:
        # Визначаємо назву
        if item.item_name == 'Інше':
            name = item.custom_name if item.custom_name else 'Інше (без назви)'
        else:
            name = item.get_item_name_display()

        qty = item.quantity
        dept = item.task.department or "Не вказано"

        # Групуємо
        if name not in stats:
            stats[name] = {'total_qty': 0, 'departments': {}}

        stats[name]['total_qty'] += qty

        if dept not in stats[name]['departments']:
            stats[name]['departments'][dept] = 0
        stats[name]['departments'][dept] += qty

    grand_total = sum(data['total_qty'] for data in stats.values())

    return render(request, 'service/report_detail.html', {
        'report': report,
        'stats': stats,
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
