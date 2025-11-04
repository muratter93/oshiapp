from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("login/success/", views.login_success, name="login_success"),  # ← この行を追加！
    path("logout/", views.logout_view, name="logout"),
    path('logout/success/', views.logout_success_view,name="logout_success")# ←これが必要！
]