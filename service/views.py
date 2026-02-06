from django.shortcuts import render
from django.http import HttpResponse
from .models import ServiceTask
from django.utils import timezone


def print_service_view(request):
    ids_param = request.GET.get('ids', '')
    if not ids_param:
        return HttpResponse("Не вибрано жодного запису", status=400)

    ids = [int(x) for x in ids_param.split(',') if x.isdigit()]

    # --- ГОЛОВНА ЗМІНА ТУТ ---
    # Фільтруємо: ID є в списку AND дата відправки пуста (ще не відправлено)
    queryset = ServiceTask.objects.filter(id__in=ids, date_sent__isnull=True)

    if not queryset.exists():
        return HttpResponse("""
            <h2 style='font-family: Arial; text-align: center; margin-top: 50px;'>
                Увага! Всі вибрані картриджі вже мають дату відправки.<br>
                У звіт нічого друкувати.
            </h2>
        """)

    # --- HTML код ---
    html = f"""
    <html>
    <head>
        <title>Звіт на заправку</title>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 12px; margin: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid black; padding: 5px; text-align: left; }}
            h2 {{ text-align: center; }}
            .no-print {{ margin-bottom: 20px; }}
            @media print {{ .no-print {{ display: none; }} }}
        </style>
    </head>
    <body>
        <div class="no-print">
            <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">🖨️ Друкувати</button>
        </div>

        <h2>Акт передачі на сервіс від {timezone.now().strftime('%d.%m.%Y')}</h2>
        <table>
            <thead>
                <tr>
                    <th>№</th>
                    <th>Назва / Модель</th>
                    <th>Відділ / Власник</th>
                    <th>Дата прийому</th>
                    <th>Тип робіт</th>
                </tr>
            </thead>
            <tbody>
    """

    for index, task in enumerate(queryset, 1):
        html += f"""
            <tr>
                <td>{index}</td>
                <td>{task.device_name}</td>
                <td>{task.department} ({task.requester_name})</td>
                <td>{task.date_received.strftime('%d.%m.%Y')}</td>
                <td>{task.get_task_type_display()}</td>
            </tr>
        """

    html += """
            </tbody>
        </table>
        <br><br>
        <div style="display: flex; justify-content: space-between; padding: 0 50px;">
            <div>
                <p><b>Здав (Замовник):</b></p>
                <br>
                <p>_______________________</p>
            </div>
            <div>
                <p><b>Прийняв (Виконавець):</b></p>
                <br>
                <p>_______________________</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)