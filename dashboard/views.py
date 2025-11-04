# dashboard/views.py
from functools import wraps
from typing import Callable
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.http import HttpRequest, HttpResponse

def staff_required(view_func: Callable) -> Callable:
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = request.user
        if not user.is_authenticated:
            login_url = f"{reverse('dashboard_login')}?next={request.get_full_path()}"
            return redirect(login_url)
        if not user.is_staff:
            return redirect('dashboard_error')
        return view_func(request, *args, **kwargs)
    return _wrapped

# 管理者ダッシュボード
@staff_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "dashboard/dashboard.html")

# アクセス拒否（権限不足）
def access_denied(request: HttpRequest) -> HttpResponse:
    return render(request, "dashboard/dashboard_error.html")

# 管理者ログイン
class DashboardLoginView(LoginView):
    template_name = "dashboard/dashboard_login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        return self.get_redirect_url() or reverse_lazy("dashboard")
