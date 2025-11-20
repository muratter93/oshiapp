from django.urls import path
from . import views

app_name = "animals"

urlpatterns = [
    path("<int:animal_id>/", views.detail, name="animal_detail"),
    path("<int:animal_id>/push/", views.push_animal, name="animal_push"),
    path("ranking/", views.ranking, name="ranking"),
]
