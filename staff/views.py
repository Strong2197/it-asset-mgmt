from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee, KepCertificate, CareerHistory
from .forms import EmployeeForm
from django.http import FileResponse, Http404
from urllib.parse import quote
import os


# Допоміжні функції залишаємо без змін
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
        'Івано-Франківський відділ (2610)', 'Яремчанський відділ (2612)',
        'Городенківський відділ (2616)', 'Долинський відділ (2617)',
        'Коломийський відділ (2619)', 'Косівський відділ (2620)',
        'Надвірнянський відділ (2621)', 'Рогатинський відділ (2622)',
        'Тисменицький відділ (2626)', 'Бухгалтерія', 'Кадри', 'Канцелярія'
    ]
    db_depts = list(Employee.objects.values_list('department', flat=True).distinct())
    all_depts = sorted(list(set(defaults + db_depts)))
    return list(filter(None, all_depts))


# --- СПИСОК ПРАЦІВНИКІВ (БЕЗ ПАГІНАЦІЇ ТА З ПОШУКОМ БЕЗ РЕГІСТРУ) ---
def staff_list(request):
    # 1. Отримуємо параметри
    query = request.GET.get('q', '').strip().lower()
    show_dismissed = request.GET.get('dismissed', 'false')

    # 2. Базова фільтрація в БД
    if show_dismissed == 'true':
        employees_qs = Employee.objects.filter(is_dismissed=True).prefetch_related('certificates')
    else:
        employees_qs = Employee.objects.filter(is_dismissed=False).prefetch_related('certificates')

    # 3. Пошук через Python (для коректної роботи з кирилицею)
    if query:
        filtered_employees = []
        for emp in employees_qs:
            # Збираємо дані для пошуку (ПІБ, Посада, Відділ, РНОКПП)
            content = f"{emp.full_name} {emp.position} {emp.department} {emp.rnokpp or ''}".lower()

            if query in content:
                filtered_employees.append(emp)
        employees = filtered_employees
    else:
        employees = list(employees_qs)

    return render(request, 'staff/staff_list.html', {
        'employees': employees,  # Тепер це весь список
        'query': query,
        'show_dismissed': show_dismissed,
        'total_count': len(employees)
    })


# Решта функцій залишається без змін (staff_create, staff_update, staff_dismiss тощо)
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
    return render(request, 'staff/staff_form.html',
                  {'form': form, 'title': 'Додати працівника', 'positions': positions, 'departments': departments})


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
            if old_position != updated_employee.position or old_department != updated_employee.department:
                CareerHistory.objects.create(
                    employee=employee, previous_position=old_position, new_position=updated_employee.position,
                    previous_department=old_department, new_department=updated_employee.department,
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
    return render(request, 'staff/staff_form.html',
                  {'form': form, 'title': 'Редагувати дані', 'employee': employee, 'positions': positions,
                   'departments': departments})


def staff_dismiss(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.is_dismissed = True
        employee.dismissal_date = request.POST.get('dismissal_date')
        employee.dismissal_order_number = request.POST.get('dismissal_order_number')
        order_file = request.FILES.get('dismissal_order_file')
        if order_file:
            employee.dismissal_order_file = order_file
            employee.dismissal_order_original_name = order_file.name
        employee.save()
    return redirect('staff_list')


def staff_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST': employee.delete()
    return redirect('staff_list')


def cert_delete(request, pk):
    cert = get_object_or_404(KepCertificate, pk=pk)
    employee_id = cert.employee.id
    cert.delete()
    return redirect('staff_update', pk=employee_id)


def open_order_file(request, pk, order_type):
    employee = get_object_or_404(Employee, pk=pk)
    if order_type == 'appointment':
        file_obj = employee.appointment_order_file
        file_name = employee.appointment_order_original_name or "appointment_order.pdf"
    else:
        file_obj = employee.dismissal_order_file
        file_name = employee.dismissal_order_original_name or "dismissal_order.pdf"
    if not file_obj or not os.path.exists(file_obj.path): raise Http404("Файл не знайдено")
    response = FileResponse(open(file_obj.path, 'rb'))
    response['Content-Disposition'] = f"inline; filename*=UTF-8''{quote(file_name)}"
    return response