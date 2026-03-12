from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Sum, Case, When, Value, IntegerField, Q
from .models import ServiceTask, ServiceReport, ServiceTaskItem, CARTRIDGE_CHOICES
from .forms import ServiceTaskForm, ServiceReportForm, ServiceItemFormSet, ServiceItemEditFormSet
from django.core.paginator import Paginator
import json
from django.views.generic import ListView
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from config.search_helpers import filter_by_text_query
from django.contrib import messages



# --- ДОПОМІЖНІ ФУНКЦІЇ ---
def get_all_departments():
    defaults = ['Бухгалтерія', 'Кадри', 'Івано-Франківський відділ']
    db_depts = list(ServiceTask.objects.values_list('department', flat=True).distinct())
    all_depts = sorted(list(set(defaults + db_depts)))
    return list(filter(None, all_depts))


def get_all_requesters():
    return list(ServiceTask.objects.values_list('requester_name', flat=True).distinct().order_by('requester_name'))


def get_last_department(request):
    name = request.GET.get('name', '').strip()
    if name:
        last_task = ServiceTask.objects.filter(requester_name__iexact=name).order_by('-created_at').first()
        if last_task:
            return JsonResponse({'found': True, 'department': last_task.department})
    return JsonResponse({'found': False})


# --- СПИСОК ЗАЯВОК ---
class ServiceTaskListView(ListView):
    model = ServiceTask
    template_name = 'service/service_list.html'
    context_object_name = 'tasks'
    paginate_by = 15

    def get_queryset(self):
        # Оптимізація запитів та ранжування статусів 
        queryset = ServiceTask.objects.prefetch_related('items').annotate(
            status_rank=Case(
                When(is_completed=False, date_sent__isnull=True, then=Value(1)),
                When(is_completed=False, date_sent__isnull=False, then=Value(2)),
                When(is_completed=True, then=Value(3)),
                default=Value(4), output_field=IntegerField(),
            )
        ).order_by('status_rank', '-date_received')

        # Фільтрація за статусом
        status_filter = self.request.GET.get('filter', 'active')
        if status_filter == 'active':
            queryset = queryset.filter(is_completed=False)
        elif status_filter == 'completed':
            queryset = queryset.filter(is_completed=True)

        # Пошук через хелпер [cite: 39-40]
        search_query = self.request.GET.get('q', '').strip()
        if search_query:
            return filter_by_text_query(
                queryset,
                search_query,
                lambda task: (
                    f"{task.department} {task.requester_name} {task.description} "
                    + " ".join(i.get_item_name_display() + " " + (i.custom_name or "") for i in task.items.all())
                ),
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Додаємо параметри для шаблону
        context['current_filter'] = self.request.GET.get('filter', 'active')
        context['search_query'] = self.request.GET.get('q', '').strip()
        
        # Рахуємо кількість для відображення
        qs = self.get_queryset()
        context['total_count'] = len(qs) if isinstance(qs, list) else qs.count()
        return context


def _save_service_task_form(request, *, task=None, formset_class=ServiceItemFormSet, title=''):
    departments = get_all_departments()
    requesters = get_all_requesters()

    if request.method == 'POST':
        form = ServiceTaskForm(request.POST, instance=task)
        formset = formset_class(request.POST, instance=task)
        if form.is_valid() and formset.is_valid():
            saved_task = form.save()
            formset.instance = saved_task
            formset.save()
            messages.success(request, f"Заявку для {saved_task.department} успішно збережено!") # Повідомлення
            return redirect('service_list')
    else:
        form = ServiceTaskForm(instance=task)
        formset = formset_class(instance=task)

    return render(request, 'service/service_form.html', {
        'form': form,
        'formset': formset,
        'departments': departments,
        'requesters': requesters,
        'title': title
    })


# --- СТВОРЕННЯ ЗАЯВКИ ---
def service_create(request):
    return _save_service_task_form(request, formset_class=ServiceItemFormSet, title='Створення комплексної заявки')


# --- РЕДАГУВАННЯ ЗАЯВКИ ---
def service_update(request, pk):
    task = get_object_or_404(ServiceTask, pk=pk)
    return _save_service_task_form(request, task=task, formset_class=ServiceItemEditFormSet, title='Редагування заявки')


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


class ServiceReportListView(ListView):
    model = ServiceReport
    template_name = 'service/report_list.html'
    context_object_name = 'reports'
    paginate_by = 15

    def get_queryset(self):
        # Оптимізація: завантажуємо пов'язані завдання та рахуємо кількість картриджів одним запитом 
        return ServiceReport.objects.prefetch_related('tasks__items').annotate(
            total_items=Sum('tasks__items__quantity')
        ).order_by('-created_at')


def report_detail(request, pk):
    report = get_object_or_404(ServiceReport, pk=pk)
    items = ServiceTaskItem.objects.filter(task__in=report.tasks.all()).select_related('task')
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

        # Ініціалізація структури, якщо це новий картридж
        if name not in stats:
            stats[name] = {
                'total_qty': 0,
                'departments': {},
                'sort_index': sort_index
            }

        stats[name]['total_qty'] += qty

        # Групуємо по відділах
        if dept not in stats[name]['departments']:
            stats[name]['departments'][dept] = {'items': [], 'sum_qty': 0}

        stats[name]['departments'][dept]['items'].append(item)
        stats[name]['departments'][dept]['sum_qty'] += qty

    # Сортування
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

def send_telegram_message(chat_id, text):
    """Допоміжна функція для відправки повідомлень назад у Telegram"""
    if not settings.TELEGRAM_BOT_TOKEN:
        return

    import requests

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': chat_id, 'text': text})

def _handle_telegram_command(chat_id, user_text):
    if not user_text.startswith('/'):
        return False

    if user_text == '/start':
        welcome_msg = (
            "👋 Привіт! Я ваш розумний IT-асистент.\n\n"
            "Просто напишіть мені, що у вас сталося або що потрібно заправити, і я сам створю заявку в системі.\n\n"
            "💡 *Приклад:* 'Це бухгалтерія, зажувало папір у принтері hp 1102' або '2610, потрібно два картриджі 85a'."
        )
        send_telegram_message(chat_id, welcome_msg)
    else:
        send_telegram_message(chat_id, "🤖 Я поки що не розумію спеціальних команд. Просто опишіть проблему звичайним текстом.")

    return True


def _build_cartridges_text():
    return "\n".join(f"- {c[0]}" for c in CARTRIDGE_CHOICES)


def _build_ai_prompt(user_text, cartridges_text):
    return """
                Ти розумний IT-асистент. Витягни дані з повідомлення і поверни ТІЛЬКИ валідний JSON.
                Повідомлення: "{user_text}"

                Ось точний список можливих позицій (item_name):
                {cartridges_text}
                - Інше

                Правила розбору:
                1. Проаналізуй повідомлення. Якщо це просто привітання ("Привіт", "Дякую"), розмова або в тексті НЕМАЄ скарги на техніку чи прохання щось заправити/відремонтувати — встанови поле "is_valid_request" у false.
                2. Якщо це реальна заявка — встанови "is_valid_request" у true і заповни дані:
                3. Зістав назву картриджа з найближчим аналогом зі списку.
                4. Якщо вказано ПРИНТЕР або пристрій — створюй ОКРЕМУ позицію. Для принтерів став "item_name": "Інше", а назву пиши в "custom_name".
                5. Якщо є скарга (наприклад "гуде", "не бере папір"), обов'язково запиши це в поле "note" для цієї позиції.
                6. "task_type" обирай 'refill' (якщо є картриджі) або 'repair'.

                Формат JSON:
                {{
                    "is_valid_request": true,
                    "task_type": "refill",
                    "requester_name": "Ім'я або номер",
                    "department": "Назва відділу",
                    "description": "",
                    "items": [
                        {{
                            "item_name": "Точна назва зі списку або 'Інше'",
                            "quantity": 1,
                            "custom_name": "Назва пристрою (якщо Інше)",
                            "note": "Скарга на пристрій (якщо є)"
                        }}
                    ]
                }}
                """.format(user_text=user_text, cartridges_text=cartridges_text)


def _extract_ai_data_from_message(user_text):
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = next((m for m in available_models if 'flash' in m), available_models[0])
    model = genai.GenerativeModel(model_name)

    prompt = _build_ai_prompt(user_text, _build_cartridges_text())
    try:
        response = model.generate_content(prompt)
        # Більш надійне очищення JSON блоків
        cleaned_text = response.text.strip()
        if '```json' in cleaned_text:
            cleaned_text = cleaned_text.split('```json')[1].split('```')[0].strip()
        elif '```' in cleaned_text:
            cleaned_text = cleaned_text.split('```')[1].split('```')[0].strip()
            
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"AI Parsing Error: {e}")
        return {"is_valid_request": False}


def _create_service_task_from_ai(ai_data):
    task = ServiceTask.objects.create(
        task_type=ai_data.get('task_type', 'refill'),
        requester_name=ai_data.get('requester_name', ''),
        department=ai_data.get('department', 'Не вказано'),
        description=ai_data.get('description', ''),
    )

    items_text_for_reply = ""
    for item in ai_data.get('items', []):
        ServiceTaskItem.objects.create(
            task=task,
            item_name=item.get('item_name') or 'Інше',
            quantity=item.get('quantity') or 1,
            custom_name=item.get('custom_name') or '',
            note=item.get('note') or '',
        )

        display_name = (item.get('custom_name') or '') if item.get('item_name') == 'Інше' else item.get('item_name')
        note_text = f" ({item.get('note')})" if item.get('note') else ""
        items_text_for_reply += f"\n🖨 {display_name} - {item.get('quantity')} шт.{note_text}"

    return task, items_text_for_reply

@csrf_exempt
def telegram_webhook(request):
    """Головний обробник повідомлень від Telegram"""
    if request.method == 'POST':
        if not settings.GEMINI_API_KEY:
            return JsonResponse({'status': 'ok'})
        try:
            # Отримуємо дані від Telegram
            data = json.loads(request.body)

            # Якщо це звичайне текстове повідомлення
            if 'message' in data and 'text' in data['message']:
                chat_id = data['message']['chat']['id']
                user_text = data['message']['text']

                if _handle_telegram_command(chat_id, user_text):
                    return JsonResponse({'status': 'ok'})  # Зупиняємо виконання, щоб не йти до ШІ

                send_telegram_message(chat_id, "⏳ Думаю... Формую заявку та підбираю картриджі...")
                ai_data = _extract_ai_data_from_message(user_text)

                if not ai_data.get('is_valid_request', True):
                    send_telegram_message(chat_id, "🤷‍♂️ Я не знайшов у вашому повідомленні інформації для створення заявки (наприклад, опису проблеми чи назви картриджа). Будь ласка, уточніть, що саме сталося.")
                    return JsonResponse({'status': 'ok'})

                task, items_text_for_reply = _create_service_task_from_ai(ai_data)
                reply_text = f"✅ Заявку №{task.id} успішно створено!\n🏢 Відділ: {task.department}\n👤 Замовник: {task.requester_name}\n{items_text_for_reply}"
                send_telegram_message(chat_id, reply_text)
            else:
                return JsonResponse({'status': 'ok'})

        except Exception as e:
            # Якщо щось пішло не так (наприклад, ШІ повернув кривий JSON)
            print(f"Помилка Webhook: {e}")
            if 'chat_id' in locals():
                send_telegram_message(chat_id, f"❌ Сталася помилка при обробці: {str(e)}")

    # Завжди повертаємо 200 OK, інакше Telegram буде дублювати повідомлення
    return JsonResponse({'status': 'ok'})