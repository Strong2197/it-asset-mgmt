from django.shortcuts import render, redirect, get_object_or_404
from .models import Employee, KepCertificate
from .forms import EmployeeForm
from django.db.models import Q


def staff_list(request):
    query = request.GET.get('q', '')
    employees = Employee.objects.all().prefetch_related('certificates')  # Оптимізація запитів

    if query:
        employees = employees.filter(
            Q(full_name__icontains=query) |
            Q(position__icontains=query) |
            Q(department__icontains=query) |
            Q(rnokpp__icontains=query)
        )

    return render(request, 'staff/staff_list.html', {'employees': employees, 'query': query})


def staff_create(request):
    positions = Employee.objects.values_list('position', flat=True).distinct()
    departments = Employee.objects.values_list('department', flat=True).distinct()
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            files = request.FILES.getlist('kep_files')
            for f in files:
                KepCertificate.objects.create(employee=employee, file=f)
            return redirect('staff_list')
    else:
        form = EmployeeForm()

    # ПОМИЛКА ТУТ: перевірте, щоб було 'staff/staff_form.html'
    # Якщо там написано 'staff/staff_list.html' — змініть на:
    return render(request, 'staff/staff_form.html', {
        'form': form,
        'title': 'Додати працівника',
        'positions': positions,  # Передаємо в шаблон
        'departments': departments  # Передаємо в шаблон
    })
def staff_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    positions = Employee.objects.values_list('position', flat=True).distinct()
    departments = Employee.objects.values_list('department', flat=True).distinct()
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            # Обробляємо файли
            # У views.py всередині staff_create та staff_update:
            files = request.FILES.getlist('kep_files')
            for f in files:
                KepCertificate.objects.create(
                    employee=employee,
                    file=f,
                    original_name=f.name  # Зберігаємо початкове ім'я файлу
                )
            return redirect('staff_list')
        else:
            # ЦЕ ВИВЕДЕ ПРИЧИНУ ПОМИЛКИ В КОНСОЛЬ
            print("ПОМИЛКИ ФОРМИ:", form.errors)
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'staff/staff_form.html', {
        'form': form,
        'title': 'Редагувати дані',
        'employee': employee,
        'positions': positions,
        'departments': departments
    })


def staff_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
    return redirect('staff_list')


# Нова функція: видалення конкретного файлу
def cert_delete(request, pk):
    cert = get_object_or_404(KepCertificate, pk=pk)
    employee_id = cert.employee.id
    cert.delete()
    return redirect('staff_update', pk=employee_id)