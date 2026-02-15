# staff/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee, KepCertificate, CareerHistory
from .forms import EmployeeForm
from django.db.models import Q
from django.http import FileResponse, Http404
from urllib.parse import quote
import os
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # <--- ІМПОРТ


# ... (функції get_all_positions та get_all_departments залишаються без змін) ...
def get_all_positions():
    defaults = [
        'Начальник управління', 'Начальник відділу', 'Заступник начальника відділу',
        'Головний спеціаліст', 'Провідний спеціаліст', 'Провідний інспектор'
    ]
    db_positions = list(Employee.objects.values_list('position', flat=True).distinct())
    all_pos = sorted(list(set(defaults + db_positions)))
    return list(filter(None, all_pos))


def get_all_departments():
    defaults = [
        'Івано-Франківський відділ (2610)',
        'Яремчанський відділ (2612)',
        'Городенківський відділ (2616)',
        'Долинський відділ (2617)',
        'Коломийський відділ (2619)',
        'Косівський відділ (2620)',
        'Надвірнянський відділ (2621)',
        'Рогатинський відділ (2622)',
        'Тисменицький відділ (2626)',
        'Бухгалтерія', 'Кадри', 'Канцелярія'
    ]
    db_depts = list(Employee.objects.values_list('department', flat=True).distinct())
    all_depts = sorted(list(set(defaults + db_depts)))
    return list(filter(None, all_depts))


# --- СПИСОК (ОНОВЛЕНО) ---
def staff_list(request):
    query = request.GET.get('q', '').strip()
    show_dismissed = request.GET.get('dismissed', 'false')

    # 1. Базова фільтрація (Активні/Звільнені)
    if show_dismissed == 'true':
        employees = Employee.objects.filter(is_dismissed=True).prefetch_related('certificates')
    else:
        employees = Employee.objects.filter(is_dismissed=False).prefetch_related('certificates')

    # 2. Серверний пошук
    if query:
        employees = employees.filter(
            Q(full_name__icontains=query) |
            Q(position__icontains=query) |
            Q(department__icontains=query) |
            Q(rnokpp__icontains=query)
        )

    # 3. ПАГІНАЦІЯ (50 елементів)
    paginator = Paginator(employees, 50)
    page = request.GET.get('page')

    try:
        employees_page = paginator.page(page)
    except PageNotAnInteger:
        employees_page = paginator.page(1)
    except EmptyPage:
        employees_page = paginator.page(paginator.num_pages)

    return render(request, 'staff/staff_list.html', {
        'employees': employees_page,
        'query': query,
        'show_dismissed': show_dismissed,
        'total_count': paginator.count
    })


# ... (решта функцій: staff_create, staff_update, staff_dismiss, staff_delete і т.д. без змін) ...
def staff_create(request):
    positions = get_all_positions()
    departments = get_all_departments()

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save(commit=False)
            if 'appointment_order_file' in request.FILES:
                employee.appointment_order_original_name = request.FILES['appointment_order_file'].name
            if 'dismissal_order_file' in request.FILES:
                employee.dismissal_order_original_name = request.FILES['dismissal_order_file'].name
            employee.save()

            files = request.FILES.getlist('kep_files')
            for f in files:
                KepCertificate.objects.create(employee=employee, file=f, original_name=f.name)
            return redirect('staff_list')
    else:
        form = EmployeeForm()

    return render(request, 'staff/staff_form.html', {
        'form': form,
        'title': 'Додати працівника',
        'positions': positions,
        'departments': departments
    })


def staff_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)

    old_position = employee.position
    old_department = employee.department

    positions = get_all_positions()
    departments = get_all_departments()

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            updated_employee = form.save(commit=False)

            pos_changed = old_position != updated_employee.position
            dept_changed = old_department != updated_employee.department

            if pos_changed or dept_changed:
                CareerHistory.objects.create(
                    employee=employee,
                    previous_position=old_position,
                    new_position=updated_employee.position,
                    previous_department=old_department,
                    new_department=updated_employee.department,
                    notes="Зміна кадрових даних"
                )

            if 'appointment_order_file' in request.FILES:
                updated_employee.appointment_order_original_name = request.FILES['appointment_order_file'].name
            if 'dismissal_order_file' in request.FILES:
                updated_employee.dismissal_order_original_name = request.FILES['dismissal_order_file'].name

            updated_employee.save()

            files = request.FILES.getlist('kep_files')
            for f in files:
                KepCertificate.objects.create(employee=employee, file=f, original_name=f.name)
            return redirect('staff_list')
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'staff/staff_form.html', {
        'form': form,
        'title': 'Редагувати дані',
        'employee': employee,
        'positions': positions,
        'departments': departments
    })


def staff_dismiss(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        date = request.POST.get('dismissal_date')
        order_num = request.POST.get('dismissal_order_number')
        order_file = request.FILES.get('dismissal_order_file')

        employee.is_dismissed = True
        if date: employee.dismissal_date = date
        if order_num: employee.dismissal_order_number = order_num

        if order_file:
            employee.dismissal_order_file = order_file
            employee.dismissal_order_original_name = order_file.name

        employee.save()
    return redirect('staff_list')


def staff_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
    return redirect('staff_list')


def cert_delete(request, pk):
    cert = get_object_or_404(KepCertificate, pk=pk)
    employee_id = cert.employee.id
    cert.delete()
    return redirect('staff_update', pk=employee_id)


def open_order_file(request, pk, order_type):
    employee = get_object_or_404(Employee, pk=pk)
    file_obj = None
    file_name = "document.pdf"

    if order_type == 'appointment':
        file_obj = employee.appointment_order_file
        file_name = employee.appointment_order_original_name or "appointment_order.pdf"
    elif order_type == 'dismissal':
        file_obj = employee.dismissal_order_file
        file_name = employee.dismissal_order_original_name or "dismissal_order.pdf"

    if not file_obj or not os.path.exists(file_obj.path):
        raise Http404("Файл не знайдено на сервері")

    response = FileResponse(open(file_obj.path, 'rb'))
    response['Content-Disposition'] = f"inline; filename*=UTF-8''{quote(file_name)}"
    return response