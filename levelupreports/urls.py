from django.urls import path
from .views import UserGameList

urlpatterns = [
    path('reports/usergames', UserGameList.as_view()),
]
