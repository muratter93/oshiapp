# dashboard/views.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

# 独自: staff だけ通す（未ログインや staff 以外は /dashboard/login/ へ）
staff_required = user_passes_test(
    lambda u: u.is_authenticated and u.is_staff,
    login_url='dashboard_login'
)

# 管理者ダッシュボード
@staff_required
def admin_dashboard(request):
    return render(request, "dashboard/dashboard.html")

# 管理者ログインページ
class DashboardLoginView(LoginView):
    template_name = 'dashboard/dashboard_login.html'
    redirect_authenticated_user = True  # 既にログイン済みならダッシュボードへ

    def get_success_url(self):
        return reverse_lazy('dashboard')
