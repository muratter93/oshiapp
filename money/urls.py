from django.urls import path
from . import views

app_name = "money"

urlpatterns = [
    path("charge/", views.charge, name="charge"),
    path("charge/buy/<int:coins>/", views.buy_coins, name="buy"),
    path('purchase-history/', views.purchase_history, name='purchase_history'),
    
]
