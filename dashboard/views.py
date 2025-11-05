# dashboard/views.py
from functools import wraps
from typing import Callable

from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView

User = get_user_model()

# ==============================================
# 認証・権限関連（装飾子）
# ==============================================
def staff_required(view_func: Callable) -> Callable:
    """管理者(スタッフ)のみアクセス許可するデコレーター"""
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = request.user
        if not user.is_authenticated:
            login_url = f"{reverse('dashboard:dashboard_login')}?next={request.get_full_path()}"
            return redirect(login_url)
        if not user.is_staff:
            return redirect('dashboard:dashboard_error')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ==============================================
# ダッシュボード本体
# ==============================================
@staff_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    """管理者ダッシュボード"""
    return render(request, "dashboard/dashboard.html")


def access_denied(request: HttpRequest) -> HttpResponse:
    """アクセス拒否（権限不足）"""
    return render(request, "dashboard/dashboard_error.html")


class DashboardLoginView(LoginView):
    """管理者ログイン画面"""
    template_name = "dashboard/dashboard_login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        return self.get_redirect_url() or reverse("dashboard:dashboard")


# ==============================================
# 管理者一覧 (is_staff=True のみ表示)
# ==============================================
@method_decorator(staff_member_required, name="dispatch")
class StaffListView(ListView):
    """管理者一覧ビュー (is_staff=Trueのみ表示)"""
    model = User
    template_name = "dashboard/admins_list.html"
    context_object_name = "users"
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.filter(is_staff=True)
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
        # ソート
        allowed = {"username", "email", "last_login", "-username", "-email", "-last_login"}
        order = self.request.GET.get("order", "username")
        if order not in allowed:
            order = "username"
        return qs.order_by(order)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "").strip()
        ctx["order"] = self.request.GET.get("order", "username")
        return ctx


# ==============================================
# 権限トグル / 削除（安全なPOSTのみ）
# ==============================================
def _is_staff_user(u) -> bool:
    return u.is_authenticated and u.is_staff

@require_POST
@staff_required
def toggle_staff(request: HttpRequest, pk: int) -> HttpResponse:
    """is_staff の ON/OFF（対象が superuser / 自分なら不可）"""
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.warning(request, "自分自身の is_staff は変更できません。")
        return redirect('dashboard:admins_list')
    if target.is_superuser:
        messages.warning(request, "superuser の is_staff は変更できません。")
        return redirect('dashboard:admins_list')

    target.is_staff = not target.is_staff
    target.save(update_fields=["is_staff"])
    messages.success(request, f"{target.username} の is_staff を {target.is_staff} に変更しました。")
    return redirect('dashboard:admins_list')


@require_POST
@staff_required
def toggle_keeper(request: HttpRequest, pk: int) -> HttpResponse:
    """is_keeper の ON/OFF（自分は不可 / フィールド存在チェック）"""
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.warning(request, "自分自身の is_keeper は変更できません。")
        return redirect('dashboard:admins_list')
    if not hasattr(target, "is_keeper"):
        messages.error(request, "このユーザーには is_keeper フィールドがありません。")
        return redirect('dashboard:admins_list')

    target.is_keeper = not target.is_keeper
    target.save(update_fields=["is_keeper"])
    messages.success(request, f"{target.username} の is_keeper を {target.is_keeper} に変更しました。")
    return redirect('dashboard:admins_list')


@require_POST
@staff_required
def delete_user(request: HttpRequest, pk: int) -> HttpResponse:
    """ユーザー削除（superuser / 自分は不可）"""
    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.warning(request, "自分自身は削除できません。")
        return redirect('dashboard:admins_list')
    if target.is_superuser:
        messages.warning(request, "superuser は削除できません。")
        return redirect('dashboard:admins_list')

    username = target.username
    target.delete()
    messages.success(request, f"{username} を削除しました。")
    return redirect('dashboard:admins_list')


@require_POST
@staff_required
def toggle_superuser(request: HttpRequest, pk: int) -> HttpResponse:
    """is_superuser の ON/OFF（操作者が superuser のときのみ / 自分は不可）"""
    if not request.user.is_superuser:
        messages.error(request, "superuser 権限が必要です。")
        return redirect('dashboard:admins_list')

    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.warning(request, "自分自身の superuser はここでは変更できません。")
        return redirect('dashboard:admins_list')

    target.is_superuser = not target.is_superuser
    # superuser を付与する場合は is_staff も整合を取る
    if target.is_superuser and not target.is_staff:
        target.is_staff = True
        target.save(update_fields=["is_superuser", "is_staff"])
    else:
        target.save(update_fields=["is_superuser"])

    messages.success(request, f"{target.username} の is_superuser を {target.is_superuser} に変更しました。")
    return redirect('dashboard:admins_list')
