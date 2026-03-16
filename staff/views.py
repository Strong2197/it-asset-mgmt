from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse, Http404
from django.urls import reverse_lazy
from django.views.generic import DeleteView
from urllib.parse import quote
import os

from config.search_helpers import filter_by_text_query
from .models import Employee, KepCertificate
from .forms import EmployeeForm, KepCertificateFormSet

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
            lambda emp: f"{emp.full_name} {emp.position} {emp.department} {emp.rnokpp or ''}"
        )
    else:
        emp_list = list(employees_qs)

    from django.core.paginator import Paginator
    paginator = Paginator(emp_list, 30)
    page = request.GET.get('page')
    employees_page = paginator.get_page(page)

    return render(request, 'staff/staff_list.html', {
        'employees': employees_page,
        'query': query,
        'show_dismissed': show_dismissed,
        'total_count': paginator.count
    })

def get_all_positions():
    defaults = ['Начальник управління', 'Начальник відділу', 'Головний спеціаліст', 'Провідний спеціаліст']
    db_positions = list(Employee.objects.values_list('position', flat=True).distinct())
    return sorted(list(filter(None, set(defaults + db_positions))))

def get_all_departments():
    defaults = ['Івано-Франківський відділ (2610)', 'Калуський відділ (2618)', 'Коломийський відділ (2619)']
    db_depts = list(Employee.objects.values_list('department', flat=True).distinct())
    return sorted(list(filter(None, set(defaults + db_depts))))

def staff_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        formset = KepCertificateFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            employee = form.save()
            formset.instance = employee
            formset.save()
            
            for f in request.FILES.getlist('kep_files'):
                KepCertificate.objects.create(employee=employee, file=f)
                
            messages.success(request, f"Працівника {employee.full_name} успішно додано!")
            return redirect('staff_list')
    else:
        form = EmployeeForm()
        formset = KepCertificateFormSet()

    return render(request, 'staff/staff_form.html', {
        'form': form, 'formset': formset, 'title': 'Додати працівника',
        'positions': get_all_positions(), 'departments': get_all_departments()
    })

def staff_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee)
        formset = KepCertificateFormSet(request.POST, request.FILES, instance=employee)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            
            for f in request.FILES.getlist('kep_files'):
                KepCertificate.objects.create(employee=employee, file=f)
                
            messages.success(request, f"Дані працівника {employee.full_name} оновлено.")
            return redirect('staff_list')
    else:
        form = EmployeeForm(instance=employee)
        formset = KepCertificateFormSet(instance=employee)

    return render(request, 'staff/staff_form.html', {
        'form': form, 'formset': formset, 'employee': employee, 'title': 'Редагувати дані',
        'positions': get_all_positions(), 'departments': get_all_departments()
    })

def staff_dismiss(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.is_dismissed = True
        employee.dismissal_date = request.POST.get('dismissal_date')
        employee.dismissal_order_number = request.POST.get('dismissal_order_number')
        if 'dismissal_order_file' in request.FILES:
            employee.dismissal_order_file = request.FILES['dismissal_order_file']
        employee.save()
    return redirect('staff_list')

def open_order_file(request, pk, order_type):
    employee = get_object_or_404(Employee, pk=pk)
    file_obj = employee.appointment_order_file if order_type == 'appointment' else employee.dismissal_order_file
    file_name = (employee.appointment_order_original_name if order_type == 'appointment' 
                 else employee.dismissal_order_original_name) or "order.pdf"
    
    if not file_obj or not os.path.exists(file_obj.path):
        raise Http404("Файл не знайдено")
        
    response = FileResponse(open(file_obj.path, 'rb'))
    response['Content-Disposition'] = f"inline; filename*=UTF-8''{quote(file_name)}"
    return response

class StaffDeleteView(DeleteView):
    model = Employee
    success_url = reverse_lazy('staff_list')

class CertDeleteView(DeleteView):
    model = KepCertificate
    def get_success_url(self):
        return reverse_lazy('staff_update', kwargs={'pk': self.object.employee.id})
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        return redirect(success_url)
