from django.urls import path
from . import views

app_name = "pages" 

urlpatterns = [
    path("about/", views.about, name="about"),
    path("about_in/", views.structure, name="about_in"),
    path("structure/", views.structure, name="structure"),
]