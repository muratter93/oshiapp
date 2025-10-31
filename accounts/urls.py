from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("login/success/", views.login_success, name="login_success"),  # ← この行を追加！
     path("logout/", auth_views.LogoutView.as_view(next_page="accounts:logout_done"), name="logout"),
    path('logout/done/', views.logout_done,name="logout_done")# ←これが必要！
]