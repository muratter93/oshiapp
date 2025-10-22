# urls.py（goods アプリの中）
from django.urls import path
from . import views
from .views import goods_list_view

app_name = 'goods'

urlpatterns = [
    path('', goods_list_view, name='list'),
    
    path("charge/", views.charge, name="charge"),
]




