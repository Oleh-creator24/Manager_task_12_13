from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
import datetime
from .models import Task, Status, SubTask  # <— SubTask нужен
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from .serializers import (TaskCreateSerializer, SubTaskCreateSerializer, SubTaskDetailSerializer,
                          TaskDetailSerializer,)
from django.db.models.functions import ExtractWeekDay
from django.http import JsonResponse
from .serializers import TaskShallowSerializer
from django.db.models.functions import ExtractWeekDay
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_http_methods
from django.db.models.functions import ExtractWeekDay

from .utils import json_ok, json_error, parse_json_body



def task_list_html(request):
    from .models import Task
    tasks = Task.objects.all()
    return render(request, 'tasks/task_list.html', {'tasks': tasks})



@csrf_exempt
@require_http_methods(["POST"])
def api_create_task(request):
    """API эндпоинт для создания задачи (ввод/вывод строго UTF-8 JSON)."""
    from .models import Task, Status

    ok, data = parse_json_body(request)
    if not ok:
        return json_error(data, status=400)

    title = data.get('title')
    deadline = data.get('deadline')
    if not title:
        return json_error({'error': 'Title is required'}, status=400)
    if not deadline:
        return json_error({'error': 'Deadline is required'}, status=400)

    status_name = data.get('status', 'To Do')
    status, _ = Status.objects.get_or_create(name=status_name)

    task = Task.objects.create(
        title=title,
        description=data.get('description', ''),
        status=status,
        deadline=deadline,
    )
    task.refresh_from_db()

    return json_ok({
        'message': 'Task created successfully',
        'task': {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status.name,
            'deadline': task.deadline.isoformat() if task.deadline else None,
        }
    }, status=201)
# def api_create_task(request):
#     """API эндпоинт для создания задачи"""
#     try:
#         data = json.loads(request.body)
#
#         # Валидация обязательных полей
#         if not data.get('title'):
#             return JsonResponse({'error': 'Title is required'}, status=400,
#                                 json_dumps_params={'ensure_ascii': False})
#
#         if not data.get('deadline'):
#             return JsonResponse({'error': 'Deadline is required'}, status=400,
#                                 json_dumps_params={'ensure_ascii': False})
#
#         # Упрощенная обработка даты - просто передаем строку, Django сам преобразует
#         deadline_str = data['deadline']
#
#         # Получаем или создаем статус
#         status_name = data.get('status', 'To Do')
#         status, created = Status.objects.get_or_create(name=status_name)
#
#         # Создаем задачу - Django сам преобразует строку в datetime
#         task = Task.objects.create(
#             title=data['title'],
#             description=data.get('description', ''),
#             status=status,
#             deadline=deadline_str  # передаем как строку
#         )
#
#         # Перезагружаем задачу из БД чтобы получить преобразованный datetime
#         task.refresh_from_db()
#
#         return JsonResponse({
#             'message': 'Task created successfully',
#             'task': {
#                 'id': task.id,
#                 'title': task.title,
#                 'description': task.description,
#                 'status': task.status.name,
#                 'deadline': task.deadline.isoformat() if task.deadline else None
#             }
#         }, status=201, json_dumps_params={'ensure_ascii': False})
#
#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Invalid JSON'}, status=400,
#                             json_dumps_params={'ensure_ascii': False})
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500,
#                             json_dumps_params={'ensure_ascii': False})

@require_http_methods(["GET"])
def api_task_list(request):
    """Список задач (фильтры/сортировки как у тебя были)."""
    from django.utils import timezone
    from .models import Task

    tasks = Task.objects.all().order_by('-deadline')
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status__name=status_filter)

    overdue = request.GET.get('overdue')
    if overdue and overdue.lower() == 'true':
        tasks = tasks.filter(deadline__lt=timezone.now())

    tasks_data = []
    now = timezone.now()
    for t in tasks:
        tasks_data.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status.name,
            'deadline': t.deadline.isoformat() if t.deadline else None,
            'is_overdue': bool(t.deadline and t.deadline < now)
        })

    return json_ok({
        'tasks': tasks_data,
        'count': len(tasks_data),
        'filters': {'status': status_filter, 'overdue': overdue}
    })

# def api_task_list(request):
#     """API для получения списка задач"""
#     tasks = Task.objects.all()
#
#     tasks_data = []
#     for task in tasks:
#         tasks_data.append({
#             'id': task.id,
#             'title': task.title,
#             'description': task.description,
#             'status': task.status.name,
#             'deadline': task.deadline.isoformat() if task.deadline else None
#         })

    return JsonResponse({'tasks': tasks_data}, json_dumps_params={'ensure_ascii': False})


@require_http_methods(["GET"])
def api_task_detail(request, task_id):
    """Детали задачи + подзадачи."""
    from django.shortcuts import get_object_or_404
    from .models import Task

    task = get_object_or_404(Task, id=task_id)
    data = {
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status.name,
        'deadline': task.deadline.isoformat() if task.deadline else None,
        'subtasks': [
            {
                'id': s.id,
                'title': s.title,
                'description': s.description,
                'status': s.status.name,
                'deadline': s.deadline.isoformat() if s.deadline else None,
            }
            for s in task.subtasks.all()
        ],
    }
    return json_ok(data)


@require_http_methods(["GET"])
def api_task_list(request):
    """API для получения списка задач с возможностью фильтрации"""
    tasks = Task.objects.all().order_by('-deadline')

    # Фильтрация по статусу (если передан параметр status)
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status__name=status_filter)

    # Фильтрация по просроченным задачам
    overdue = request.GET.get('overdue')
    if overdue and overdue.lower() == 'true':
        tasks = tasks.filter(deadline__lt=timezone.now())

    tasks_data = []
    for task in tasks:
        tasks_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status.name,
            'deadline': task.deadline.isoformat() if task.deadline else None,
            'is_overdue': task.deadline < timezone.now() if task.deadline else False
        })

    return JsonResponse({
        'tasks': tasks_data,
        'count': len(tasks_data),
        'filters': {
            'status': status_filter,
            'overdue': overdue
        }
    }, json_dumps_params={'ensure_ascii': False})


@require_http_methods(["GET"])
def api_task_stats(request):
    """API для получения расширенной статистики по задачам"""
    # Базовые метрики
    total_tasks = Task.objects.count()
    total_subtasks = SubTask.objects.count()

    # Статистика по статусам задач
    tasks_by_status = Task.objects.values('status__name').annotate(count=Count('id'))
    status_stats = {item['status__name']: item['count'] for item in tasks_by_status}

    # Статистика по статусам подзадач
    subtasks_by_status = SubTask.objects.values('status__name').annotate(count=Count('id'))
    subtask_status_stats = {item['status__name']: item['count'] for item in subtasks_by_status}

    # Просроченные задачи
    overdue_tasks = Task.objects.filter(deadline__lt=timezone.now()).count()
    overdue_subtasks = SubTask.objects.filter(deadline__lt=timezone.now()).count()

    # Задачи без описания
    tasks_without_description = Task.objects.filter(description='').count()
    subtasks_without_description = SubTask.objects.filter(description='').count()

    # Ближайшие дедлайны (3 ближайшие задачи)
    upcoming_tasks = Task.objects.filter(deadline__gte=timezone.now()).order_by('deadline')[:3]
    upcoming_tasks_data = [
        {
            'id': task.id,
            'title': task.title,
            'deadline': task.deadline.isoformat(),
            'days_until': (task.deadline - timezone.now()).days
        }
        for task in upcoming_tasks
    ]

    # Заполняем нулевые значения для всех статусов
    all_statuses = ['To Do', 'In Progress', 'Done']
    for status in all_statuses:
        if status not in status_stats:
            status_stats[status] = 0
        if status not in subtask_status_stats:
            subtask_status_stats[status] = 0

    return JsonResponse({
        'stats': {
            'tasks': {
                'total': total_tasks,
                'by_status': status_stats,
                'overdue': overdue_tasks,
                'without_description': tasks_without_description,
            },
            'subtasks': {
                'total': total_subtasks,
                'by_status': subtask_status_stats,
                'overdue': overdue_subtasks,
                'without_description': subtasks_without_description,
            },
            'upcoming_deadlines': upcoming_tasks_data,
        },
        'timestamp': timezone.now().isoformat(),
        'success': True
    }, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
@require_http_methods(["POST"])
def api_create_subtask(request):
    """API эндпоинт для создания подзадачи"""
    try:
        data = json.loads(request.body)

        # Базовая валидация
        if not data.get('title'):
            return JsonResponse({'error': 'Title is required'}, status=400,
                                json_dumps_params={'ensure_ascii': False})

        if not data.get('deadline'):
            return JsonResponse({'error': 'Deadline is required'}, status=400,
                                json_dumps_params={'ensure_ascii': False})

        # Валидируем и сохраняем через сериализатор (task_id и status_id обрабатываются внутри)
        serializer = SubTaskCreateSerializer(data=data)
        if serializer.is_valid():
            subtask = serializer.save()
            return JsonResponse({
                'message': 'SubTask created successfully',
                'subtask': {
                    'id': subtask.id,
                    'title': subtask.title,
                    'description': subtask.description,
                    'status': subtask.status.name,
                    'deadline': subtask.deadline.isoformat() if subtask.deadline else None,
                    'task_id': subtask.task.id,
                    'created_at': subtask.created_at.isoformat() if subtask.created_at else None
                }
            }, status=201, json_dumps_params={'ensure_ascii': False})
        else:
            return JsonResponse({'error': serializer.errors}, status=400,
                                json_dumps_params={'ensure_ascii': False})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400,
                            json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500,
                            json_dumps_params={'ensure_ascii': False})


@require_http_methods(["GET"])
def api_subtask_detail(request, subtask_id):
    """API для получения деталей подзадачи по ID"""
    subtask = get_object_or_404(SubTask, id=subtask_id)
    serializer = SubTaskDetailSerializer(subtask)
    return JsonResponse(serializer.data, json_dumps_params={'ensure_ascii': False})


@require_http_methods(["GET"])
def api_task_subtasks(request, task_id):
    """API для получения всех подзадач конкретной задачи"""
    task = get_object_or_404(Task, id=task_id)
    subtasks = task.subtasks.all()

    serializer = SubTaskDetailSerializer(subtasks, many=True)
    return JsonResponse({'subtasks': serializer.data, 'task_id': task_id},
                        json_dumps_params={'ensure_ascii': False})
# маппинг названия дня к номеру для ExtractWeekDay (1=Sunday ... 7=Saturday)
DAY_MAPS = {
    "понедельник": 2, "вторник": 3, "среда": 4, "четверг": 5, "пятница": 6, "суббота": 7, "воскресенье": 1,
    "понеділок": 2, "вівторок": 3, "середа": 4, "четвер": 5, "пʼятниця": 6, "пятниця": 6, "субота": 7, "неділя": 1,
    "monday": 2, "tuesday": 3, "wednesday": 4, "thursday": 5, "friday": 6, "saturday": 7, "sunday": 1,
}

def _parse_weekday_param(raw):
    if raw is None or str(raw).strip() == "":
        return None
    s = str(raw).strip().lower()
    if s.isdigit():
        n = int(s)
        if 0 <= n <= 6:           # Python Monday=0..Sunday=6 -> Django Sunday=1..Saturday=7
            return 1 if n == 6 else n + 2
        if 1 <= n <= 7:
            return n
    return DAY_MAPS.get(s)

@require_http_methods(["GET"])
def api_tasks_by_weekday(request):
    """GET /api/tasks/by-weekday/?day=вторник — без day вернёт все задачи."""
    from .models import Task
    from .serializers import TaskShallowSerializer

    day_param = request.GET.get("day")
    wday = _parse_weekday_param(day_param)

    qs = Task.objects.all()
    if wday is not None:
        qs = qs.annotate(wd=ExtractWeekDay("deadline")).filter(wd=wday)

    data = TaskShallowSerializer(qs, many=True).data
    from django.http import JsonResponse
    return JsonResponse(
        {"count": len(data), "day": day_param, "tasks": data},
        status=200,
        json_dumps_params={"ensure_ascii": False}
    )
DAY_MAPS = {
    "понедельник": 2, "вторник": 3, "среда": 4, "четверг": 5, "пятница": 6, "суббота": 7, "воскресенье": 1,
    "понеділок": 2, "вівторок": 3, "середа": 4, "четвер": 5, "пʼятниця": 6, "пятниця": 6, "субота": 7, "неділя": 1,
    "monday": 2, "tuesday": 3, "wednesday": 4, "thursday": 5, "friday": 6, "saturday": 7, "sunday": 1,
}

def _parse_weekday_param(raw):
    if raw is None or str(raw).strip() == "":
        return None
    s = str(raw).strip().lower()
    if s.isdigit():
        n = int(s)
        if 0 <= n <= 6:           # Python Monday=0..Sunday=6 -> Django Sunday=1..Saturday=7
            return 1 if n == 6 else n + 2
        if 1 <= n <= 7:
            return n
    return DAY_MAPS.get(s)

@require_http_methods(["GET"])
def api_tasks_by_weekday(request):
    """GET /api/tasks/by-weekday/?day=вторник — без day вернёт все задачи."""
    from .models import Task
    from .serializers import TaskShallowSerializer
    from django.http import JsonResponse

    day_param = request.GET.get("day")
    wday = _parse_weekday_param(day_param)

    qs = Task.objects.all()
    if wday is not None:
        qs = qs.annotate(wd=ExtractWeekDay("deadline")).filter(wd=wday)

    data = TaskShallowSerializer(qs, many=True).data
    return JsonResponse(
        {"count": len(data), "day": day_param, "tasks": data},
        status=200,
        json_dumps_params={"ensure_ascii": False}
    )

