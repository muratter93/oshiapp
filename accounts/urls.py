from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("login/success/", views.login_success, name="login_success"),
    path("logout/", views.logout_view, name="logout"),
    path("logout/success/", views.logout_success_view, name="logout_success"),

    # パスワードリセット
    path(
        'member_password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset_form.html',
            success_url=reverse_lazy('accounts:member_password_reset_done')  # ★ここ！
        ),
        name='member_password_reset'
    ),

    path(
        'member_password_reset_done/',
        auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
        name='member_password_reset_done'
    ),

    path(
        'member_reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
        name='member_password_reset_confirm'
    ),

    path(
        'member_reset_done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
        name='member_password_reset_complete'
    ),
]
