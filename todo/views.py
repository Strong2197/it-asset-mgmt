from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Task

@login_required
def get_tasks(request):
    tasks = Task.objects.filter(user=request.user)
    data = [{"id": t.id, "text": t.text, "done": t.is_done} for t in tasks]
    return JsonResponse({"tasks": data})

@login_required
@require_POST
def add_task(request):
    text = request.POST.get('text', '').strip()
    if text:
        task = Task.objects.create(user=request.user, text=text)
        return JsonResponse({"id": task.id, "text": task.text, "done": task.is_done})
    return JsonResponse({"error": "Текст порожній"}, status=400)

@login_required
@require_POST
def toggle_task(request, pk):
    try:
        task = Task.objects.get(pk=pk, user=request.user)
        task.is_done = not task.is_done
        task.save()
        return JsonResponse({"success": True})
    except Task.DoesNotExist:
        return JsonResponse({"error": "Не знайдено"}, status=404)

@login_required
@require_POST
def delete_task(request, pk):
    Task.objects.filter(pk=pk, user=request.user).delete()
    return JsonResponse({"success": True})