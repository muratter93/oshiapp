from django.urls import path
from . import views

app_name = "animals"

urlpatterns = [
    path("<int:pk>/", views.detail, name="detail"),
]
