from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomSetPasswordForm

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
            email_template_name='accounts/password_reset_email.html',
            success_url=reverse_lazy('accounts:password_reset_done')
        ),
        name='password_reset'
    ),

    # メール送信完了ページ
    path(
        'member_password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    # リンククリック後のパスワード再設定ページ
    path(
        'member_reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('accounts:password_reset_complete'),
            form_class=CustomSetPasswordForm  # ← ここでカスタムフォームを指定
        ),
        name='password_reset_confirm'
    ),

    # パスワード再設定完了ページ
    path(
        'member_reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]
