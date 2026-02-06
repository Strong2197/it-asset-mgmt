from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import ServiceTask, ServiceReport
from .forms import ServiceTaskForm


# --- 1. Список (Головна сторінка сервісу) ---
def service_list(request):
    tasks = ServiceTask.objects.all().order_by('-date_received')
    return render(request, 'service/service_list.html', {'tasks': tasks})


# --- 2. Створення та Редагування ---
def service_create(request):
    if request.method == 'POST':
        form = ServiceTaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('service_list')
    else:
        form = ServiceTaskForm()
    return render(request, 'service/service_form.html', {'form': form, 'title': 'Нова заявка'})


def service_update(request, pk):
    task = get_object_or_404(ServiceTask, pk=pk)
    if request.method == 'POST':
        form = ServiceTaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('service_list')
    else:
        form = ServiceTaskForm(instance=task)
    return render(request, 'service/service_form.html', {'form': form, 'title': 'Редагувати заявку'})


# --- 3. ШВИДКЕ ПОВЕРНЕННЯ ---
def service_quick_return(request, pk):
    """Ставить сьогоднішню дату повернення і статус 'Завершено'"""
    task = get_object_or_404(ServiceTask, pk=pk)
    task.date_returned = timezone.now().date()
    task.is_completed = True
    task.save()
    return redirect('service_list')


# --- 4. ЛОГІКА ДРУКУ ТА ЗБЕРЕЖЕННЯ ---

def print_preview(request):
    """Показує список картриджів, готових до відправки (без дати відправки)"""
    # Знаходимо всі записи, які ще не відправлені (date_sent is Null) і не завершені
    tasks_to_print = ServiceTask.objects.filter(date_sent__isnull=True, is_completed=False)

    return render(request, 'service/print_preview.html', {'tasks': tasks_to_print})


def save_report(request):
    """Зберігає звіт у базу і проставляє дату відправки"""
    if request.method == 'POST':
        # 1. Знаходимо ті самі таски (не відправлені)
        tasks_to_save = ServiceTask.objects.filter(date_sent__isnull=True, is_completed=False)

        if not tasks_to_save.exists():
            return redirect('service_list')

        # 2. Створюємо запис в історії
        report = ServiceReport.objects.create()
        report.tasks.set(tasks_to_save)

        # 3. Оновлюємо картриджі: ставимо сьогоднішню дату відправки
        tasks_to_save.update(date_sent=timezone.now().date())

        # 4. Переходимо на сторінку перегляду вже збереженого звіту (для друку)
        return redirect('report_detail', pk=report.pk)

    return redirect('service_list')


# --- 5. ІСТОРІЯ ---

def report_list(request):
    """Список всіх збережених актів"""
    reports = ServiceReport.objects.all()
    return render(request, 'service/report_list.html', {'reports': reports})


def report_detail(request, pk):
    """Сторінка для друку конкретного збереженого акту"""
    report = get_object_or_404(ServiceReport, pk=pk)
    return render(request, 'service/report_detail.html', {'report': report})


from .forms import ServiceReportForm  # <--- Не забудьте імпортувати нову форму зверху!


def report_edit(request, pk):
    report = get_object_or_404(ServiceReport, pk=pk)

    if request.method == 'POST':
        # Запам'ятовуємо список картриджів ДО зміни
        old_tasks = list(report.tasks.all())

        form = ServiceReportForm(request.POST, instance=report)
        if form.is_valid():
            saved_report = form.save()

            # 1. Отримуємо новий список після збереження
            new_tasks = saved_report.tasks.all()

            # 2. Знаходимо ті, що БУЛИ, але ми їх ПРИБРАЛИ
            # (їм треба очистити дату відправки)
            for task in old_tasks:
                if task not in new_tasks:
                    task.date_sent = None
                    task.save()

            # 3. Знаходимо ті, що ми ДОДАЛИ
            # (їм треба поставити дату відправки, таку ж як у звіту)
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