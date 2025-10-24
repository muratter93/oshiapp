from django.urls import path
from .views import purchase_done

app_name = "subscription"

urlpatterns = [
    path("buy/<str:code>/done/", purchase_done, name="purchase_done"),
]