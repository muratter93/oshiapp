from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("login/success/", views.login_success, name="login_success"),  # ← この行を追加！
    path('logout/', auth_views.LogoutView.as_view(next_page="/"), name='logout'),  # ←これが必要！
]