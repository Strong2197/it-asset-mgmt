from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee, KepCertificate, CareerHistory
from .forms import EmployeeForm
from django.http import FileResponse, Http404
from urllib.parse import quote
from django.core.paginator import Paginator
import os
from config.view_helpers import delete_on_post
from config.search_helpers import filter_by_text_query


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
        'Тисменицький відділ (2626)',
    ]
    db_depts = list(Employee.objects.values_list('department', flat=True).distinct())
    all_depts = sorted(list(set(defaults + db_depts)))
    return list(filter(None, all_depts))


def _attach_order_original_names(employee, files):
    if 'appointment_order_file' in files:
        employee.appointment_order_original_name = files['appointment_order_file'].name
    if 'dismissal_order_file' in files:
        employee.dismissal_order_original_name = files['dismissal_order_file'].name


def _save_kep_certificates(employee, files):
    for f in files.getlist('kep_files'):
        KepCertificate.objects.create(employee=employee, file=f, original_name=f.name)


# --- СПИСОК ПРАЦІВНИКІВ (БЕЗ ПАГІНАЦІЇ ТА З ПОШУКОМ БЕЗ РЕГІСТРУ) ---
def staff_list(request):
    query = request.GET.get('q', '').strip()
    show_dismissed = request.GET.get('dismissed', 'false')

    if show_dismissed == 'true':
        employees_qs = Employee.objects.filter(is_dismissed=True).prefetch_related('certificates')
    else:
        employees_qs = Employee.objects.filter(is_dismissed=False).prefetch_related('certificates')

    if query:
        emp_list = filter_by_text_query(
            employees_qs,
            query,
            lambda emp: f"{emp.full_name} {emp.position} {emp.department} {emp.rnokpp or ''}",
        )
    else:
        emp_list = list(employees_qs)

    # ПАГІНАЦІЯ (30 на сторінку)
    paginator = Paginator(emp_list, 30)
    page = request.GET.get('page')
    employees_page = paginator.get_page(page)

    return render(request, 'staff/staff_list.html', {
        'employees': employees_page,
        'query': query,
        'show_dismissed': show_dismissed,
        'total_count': paginator.count
    })


# Решта функцій залишається без змін (staff_create, staff_update, staff_dismiss тощо)
def _staff_form_context(form, *, title, employee=None):
    context = {
        'form': form,
        'title': title,
        'positions': get_all_positions(),
        'departments': get_all_departments(),
    }
    if employee is not None:
        context['employee'] = employee
    return context


def _save_employee_form(request, *, employee=None, title=''):
    old_position = employee.position if employee else None
    old_department = employee.department if employee else None

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            saved_employee = form.save(commit=False)
            if employee and (old_position != saved_employee.position or old_department != saved_employee.department):
                CareerHistory.objects.create(
                    employee=employee,
                    previous_position=old_position,
                    new_position=saved_employee.position,
                    previous_department=old_department,
                    new_department=saved_employee.department,
                    notes="Зміна кадрових даних",
                )
            _attach_order_original_names(saved_employee, request.FILES)
            saved_employee.save()
            _save_kep_certificates(saved_employee, request.FILES)
            return redirect('staff_list')
    else:
        form = EmployeeForm(instance=employee)

    return render(
        request,
        'staff/staff_form.html',
        _staff_form_context(form, title=title, employee=employee),
    )


def staff_create(request):
    return _save_employee_form(request, title='Додати працівника')


def staff_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return _save_employee_form(request, employee=employee, title='Редагувати дані')


def staff_dismiss(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.is_dismissed = True
        employee.dismissal_date = request.POST.get('dismissal_date')
        employee.dismissal_order_number = request.POST.get('dismissal_order_number')
        if 'dismissal_order_file' in request.FILES:
            employee.dismissal_order_file = request.FILES['dismissal_order_file']
        _attach_order_original_names(employee, request.FILES)
        employee.save()
    return redirect('staff_list')


def staff_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return delete_on_post(request, obj=employee, success_url='staff_list')


def cert_delete(request, pk):
    cert = get_object_or_404(KepCertificate, pk=pk)
    employee_id = cert.employee.id
    return delete_on_post(request, obj=cert, success_url='staff_update', pk=employee_id)


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
