from django.urls import path
from . import views

app_name = "money"

urlpatterns = [
    path("charge/", views.charge, name="charge"),
    path("charge/buy/<int:coins>/", views.buy_coins, name="buy"),
    path('purchase-history/', views.purchase_history, name='purchase_history'),
    path('purchase-history2/', views.purchase_history2, name='purchase_history2'),
    path("buy/<int:coins>/", views.buy_coins, name="buy"),  # 決済後専用にする
    path("pay/execute/", views.pay_execute, name="pay_execute"),
]

