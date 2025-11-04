# dashboard/urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from django.urls import path
from .views import DashboardLoginView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', DashboardLoginView.as_view(
        # redirect_authenticated_user=True
    ), name='dashboard_login'),

path('logout/', auth_views.LogoutView.as_view(
    next_page=reverse_lazy('main:index')  # ← mainアプリのトップページへ！
), name='dashboard_logout'),

    path('', views.admin_dashboard, name='dashboard'),
]
