
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.permissions import AllowAny

from .models import SubTask
from .serializers import (
    SubTaskCreateSerializer,
    SubTaskDetailSerializer,
)

@method_decorator(csrf_exempt, name="dispatch")
class SubTaskListCreateView(APIView):
    """
    GET /api/subtasks/
      Параметры:
        - page (int, >=1), по умолчанию 1
        - page_size (опционально, но мы принудительно ограничиваем до 5)
        - task_id (int) — фильтр по задаче
        - task_title (str) — фильтр по названию задачи (contains, case-insensitive)
        - status (str) — фильтр по названию статуса подзадачи (exact, case-insensitive)
      Сортировка: по -created_at (последние сначала)
      Пагинация: не более 5 на страницу
    POST /api/subtasks/ — создать подзадачу
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        qs = SubTask.objects.all().select_related('task', 'status').order_by('-created_at')

        # ---- Задание 3: фильтрация по task_title и status ----
        task_id = request.GET.get('task_id')
        task_title = request.GET.get('task_title')
        status_name = request.GET.get('status')

        if task_id:
            qs = qs.filter(task_id=task_id)
        if task_title:
            qs = qs.filter(task__title__icontains=task_title.strip())
        if status_name:
            qs = qs.filter(status__name__iexact=status_name.strip())

        # ---- Задание 2: пагинация 5 шт. на страницу ----
        # page_size игнорируем (жёстко 5), но корректно парсим page
        def to_int(v, default):
            try:
                iv = int(v)
                return iv if iv >= 1 else default
            except Exception:
                return default

        page = to_int(request.GET.get('page'), 1)
        page_size = 5
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = list(qs[start:end])
        data = SubTaskDetailSerializer(items, many=True).data

        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": data
        }, status=http_status.HTTP_200_OK)

    def post(self, request):
        serializer = SubTaskCreateSerializer(data=request.data)
        if serializer.is_valid():
            subtask = serializer.save()
            out = SubTaskDetailSerializer(subtask).data
            return Response(out, status=http_status.HTTP_201_CREATED)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name="dispatch")
class SubTaskDetailUpdateDeleteView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_object(self, pk):
        try:
            return SubTask.objects.select_related('task', 'status').get(pk=pk)
        except SubTask.DoesNotExist:
            return None

    def get(self, request, pk: int):
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)
        return Response(SubTaskDetailSerializer(obj).data, status=http_status.HTTP_200_OK)

    def patch(self, request, pk: int):
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = SubTaskCreateSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            subtask = serializer.save()
            return Response(SubTaskDetailSerializer(subtask).data, status=http_status.HTTP_200_OK)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk: int):
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)
        serializer = SubTaskCreateSerializer(obj, data=request.data, partial=False)
        if serializer.is_valid():
            subtask = serializer.save()
            return Response(SubTaskDetailSerializer(subtask).data, status=http_status.HTTP_200_OK)
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk: int):
        obj = self.get_object(pk)
        if not obj:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)
