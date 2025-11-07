# dashboard/urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .views import DashboardLoginView, StaffCreateView, StaffUpdateView, MemberListView, MemberUpdateView

app_name = "dashboard"

urlpatterns = [
    # 認証関連
    path('login/', DashboardLoginView.as_view(), name='dashboard_login'),
    path('dashboard_error/', views.access_denied, name='dashboard_error'),
    path('logout/', auth_views.LogoutView.as_view(next_page=reverse_lazy('main:index')), name='dashboard_logout'),

    # 一覧・作成
    path('admins/', views.StaffListView.as_view(), name='admins_list'),
    path('admins/new/', StaffCreateView.as_view(), name='staff_create'),
    path('admins/<int:pk>/edit/', StaffUpdateView.as_view(), name='admin_edit'),

    # アクション系（POST）
    path('admins/<int:pk>/toggle-staff/', views.toggle_staff, name='toggle_staff'),
    path('admins/<int:pk>/toggle-keeper/', views.toggle_keeper, name='toggle_keeper'),
    path('admins/<int:pk>/toggle-superuser/', views.toggle_superuser, name='toggle_superuser'),

    # 🔽 削除 → 退会・再開に変更
    path('admins/<int:pk>/withdraw/', views.withdraw_user, name='withdraw_user'),
    path('admins/<int:pk>/reactivate/', views.reactivate_user, name='reactivate_user'),

        # --- 一般会員一覧・編集---
    path('members/', MemberListView.as_view(), name='member_list'),
    path('members/<int:pk>/edit/', MemberUpdateView.as_view(), name='member_edit'),
    path('members/<int:pk>/withdraw/', views.withdraw_member, name='withdraw_member'),
    path('members/<int:pk>/reactivate/', views.reactivate_member, name='reactivate_member'),

    # ダッシュボード本体
    path('', views.admin_dashboard, name='dashboard'),
]
