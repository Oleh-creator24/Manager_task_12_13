from django.contrib import admin
from django.urls import path, include
from tasks.views import api_tasks_by_weekday

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("tasks.urls")),
    path("api/tasks/by-weekday/", api_tasks_by_weekday, name="api_tasks_by_weekday"),
]
