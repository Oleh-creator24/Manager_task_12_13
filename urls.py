# Manager_task_12/urls.py
from django.contrib import admin
from django.urls import path, include
from tasks.views import api_tasks_by_weekday  # ← наш эндпоинт

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("tasks.urls")),  # все пути из приложения tasks
    # Прямое подключение by-weekday (на случай, если в app-urls забудем)
    path("api/tasks/by-weekday/", api_tasks_by_weekday, name="api_tasks_by_weekday"),
]
