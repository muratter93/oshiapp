from django.urls import path
from . import views

app_name = "pages" 

urlpatterns = [
    path("about/", views.structure, name="about"),
    path("structure/", views.structure, name="structure"),
]