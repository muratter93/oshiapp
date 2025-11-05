# dashboard/urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .views import DashboardLoginView

app_name = "dashboard"

urlpatterns = [
    path('login/',  DashboardLoginView.as_view(), name='dashboard_login'),
    path('dashboard_error/', views.access_denied, name='dashboard_error'),
    path('logout/', auth_views.LogoutView.as_view(next_page=reverse_lazy('main:index')), name='dashboard_logout'),

    # 一覧
    path('admins/', views.StaffListView.as_view(), name='admins_list'),

    # アクション系（POST）
    path('admins/<int:pk>/toggle-staff/', views.toggle_staff, name='toggle_staff'),
    path('admins/<int:pk>/toggle-keeper/', views.toggle_keeper, name='toggle_keeper'),
    path('admins/<int:pk>/toggle-superuser/', views.toggle_superuser, name='toggle_superuser'),
    path('admins/<int:pk>/delete/', views.delete_user, name='delete_user'),

    path('', views.admin_dashboard, name='dashboard'),
]
