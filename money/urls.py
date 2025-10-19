from django.urls import path
from . import views

app_name = "money" 

urlpatterns = [
    path("charge/", views.charge, name="charge"),
]