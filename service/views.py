from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import ServiceTask, ServiceReport
from .forms import ServiceTaskForm, ServiceReportForm
from django.utils import timezone
from django.db.models import Q

def service_receive_from_repair(request, pk):
    task = get_object_or_404(ServiceTask, pk=pk)
    task.date_back_from_service = timezone.now().date()
    task.save()
    return redirect('service_list')
# Допоміжна функція для отримання списку відділів
def get_all_departments():
    # 1. Ваші стандартні відділи
    defaults = ['Бухгалтерія', 'Кадри', 'Івано-Франківський відділ']

    # 2. Відділи, які вже є в базі (щоб не втратити інші)
    db_depts = list(ServiceTask.objects.values_list('department', flat=True).distinct())

    # 3. Об'єднуємо, прибираємо дублікати і сортуємо
    # filter(None, ...) прибирає пусті значення
    all_depts = sorted(list(set(defaults + db_depts)))
    return list(filter(None, all_depts))


# --- 1. Список ремонтів ---
def service_list(request):
    tasks = ServiceTask.objects.all().order_by('-date_received')
    return render(request, 'service/service_list.html', {'tasks': tasks})


# --- 2. Створення та Редагування ---
def service_create(request):
    departments = get_all_departments()  # <--- Отримуємо список

    if request.method == 'POST':
        form = ServiceTaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('service_list')
    else:
        form = ServiceTaskForm()

    return render(request, 'service/service_form.html', {
        'form': form,
        'title': 'Нова заявка',
        'departments': departments  # <--- Передаємо в шаблон
    })


def service_update(request, pk):
    task = get_object_or_404(ServiceTask, pk=pk)
    departments = get_all_departments()  # <--- Отримуємо список

    if request.method == 'POST':
        form = ServiceTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('service_list')
    else:
        form = ServiceTaskForm(instance=task)

    return render(request, 'service/service_form.html', {
        'form': form,
        'title': 'Редагування заявки',
        'departments': departments  # <--- Передаємо в шаблон
    })


# --- 3. ШВИДКЕ ПОВЕРНЕННЯ ---
def service_quick_return(request, pk):
    task = get_object_or_404(ServiceTask, pk=pk)
    task.date_returned = timezone.now().date()
    task.is_completed = True
    task.save()
    return redirect('service_list')


# --- 4. ЛОГІКА ДРУКУ ТА ЗБЕРЕЖЕННЯ ---
def print_preview(request):
    tasks_to_print = ServiceTask.objects.filter(date_sent__isnull=True, is_completed=False)
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


# --- 5. ІСТОРІЯ ТА РЕДАГУВАННЯ ЗВІТУ ---
def report_list(request):
    reports = ServiceReport.objects.all()
    return render(request, 'service/report_list.html', {'reports': reports})


def report_detail(request, pk):
    report = get_object_or_404(ServiceReport, pk=pk)
    return render(request, 'service/report_detail.html', {'report': report})


def report_edit(request, pk):
    report = get_object_or_404(ServiceReport, pk=pk)

    if request.method == 'POST':
        old_tasks = list(report.tasks.all())
        form = ServiceReportForm(request.POST, instance=report)
        if form.is_valid():
            saved_report = form.save()
            new_tasks = saved_report.tasks.all()

            # Логіка оновлення дат
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