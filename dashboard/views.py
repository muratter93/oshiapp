# dashboard/views.py
from functools import wraps
from typing import Callable

from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, IntegerField, Value, Case, When
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView, FormView

from django.utils import timezone
from django.contrib.sessions.models import Session

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
# 管理者一覧
# - is_staff=True をベース
# - status=all/active/inactive でフィルタ
# - 並びは「有効(0)→退会(1)」優先 + 任意ソート
# ==============================================
@method_decorator(staff_member_required, name="dispatch")
class StaffListView(ListView):
    model = User
    template_name = "dashboard/admins_list.html"
    context_object_name = "users"
    paginate_by = 20

    def _admin_base_q(self):
        # is_keeper フィールド有無を安全に判定（無い環境での FieldError 回避）
        field_names = {f.name for f in User._meta.get_fields()}
        if "is_keeper" in field_names:
            return User.objects.filter(Q(is_staff=True) | Q(is_keeper=True))
        return User.objects.filter(is_staff=True)

    def get_queryset(self):
        base = self._admin_base_q()

        # 検索
        q = (self.request.GET.get("q") or "").strip()
        if q:
            base = base.filter(Q(username__icontains=q) | Q(email__icontains=q))

        # ステータスフィルタ: all(既定)/active/inactive
        status = (self.request.GET.get("status") or "all").strip()
        if status == "active":
            base = base.filter(is_active=True)
        elif status == "inactive":
            base = base.filter(is_active=False)

        # 並び（id昇順をデフォルト）
        allowed = {"id", "-id", "username", "-username", "email", "-email", "last_login", "-last_login"}
        order = (self.request.GET.get("order") or "id").strip()
        if order not in allowed:
            order = "id"

        return base.order_by(order)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        q = (self.request.GET.get("q") or "").strip()
        order = (self.request.GET.get("order") or "id").strip()
        status = (self.request.GET.get("status") or "all").strip()

        base_all = self._admin_base_q()
        ctx.update({
            "q": q,
            "order": order if order in {"id","-id","username","-username","email","-email","last_login","-last_login"} else "id",
            "status": status,
            "counts": {
                "all": base_all.count(),
                "active": base_all.filter(is_active=True).count(),
                "inactive": base_all.filter(is_active=False).count(),
            },
        })
        return ctx


# ==============================================
# サーバー側の強制ルール
#  - 対象が superuser: 誰でも退会不可 / 編集は superuser のみ
#  - 対象が is_staff(非superuser):
#      - 操作者 superuser: 編集可・退会可（※自分退会は不可）
#      - 操作者 is_staff: 自分=編集可/退会不可、他人=編集不可/退会不可
#  - 対象が is_keeper(非superuser/非staff想定・混在許容):
#      - 操作者 superuser: 編集可・退会可（※自分退会は不可）
#      - 操作者 is_staff: 編集可・退会不可
# ==============================================
def _redirect_admins():
    return redirect('dashboard:admins_list')

def _must_superuser(request: HttpRequest) -> bool:
    if not request.user.is_superuser:
        messages.error(request, "この操作を行えるのは最高管理者のみです。")
        return False
    return True


@require_POST
@staff_required
def toggle_staff(request: HttpRequest, pk: int) -> HttpResponse:
    """
    is_staff の ON/OFF
    - 操作者: superuser のみ許可
    - 対象: 自分と superuser は変更不可
    - 退会済み（is_active=False）は操作不可
    """
    if not _must_superuser(request):
        return _redirect_admins()

    target = get_object_or_404(User, pk=pk)
    if not target.is_active:
        messages.warning(request, "退会済みユーザーは操作できません。")
        return _redirect_admins()
    if target == request.user:
        messages.warning(request, "自分自身の is_staff は変更できません。")
        return _redirect_admins()
    if target.is_superuser:
        messages.warning(request, "superuser の is_staff は変更できません。")
        return _redirect_admins()

    target.is_staff = not target.is_staff
    target.save(update_fields=["is_staff"])
    messages.success(request, f"{target.username} の is_staff を {target.is_staff} に変更しました。")
    return _redirect_admins()


@require_POST
@staff_required
def toggle_keeper(request: HttpRequest, pk: int) -> HttpResponse:
    """
    is_keeper の ON/OFF
    - 操作者: superuser のみ許可
    - 対象: 自分は不可 / フィールド未実装なら弾く
    - 退会済み（is_active=False）は操作不可
    """
    if not _must_superuser(request):
        return _redirect_admins()

    target = get_object_or_404(User, pk=pk)
    if not target.is_active:
        messages.warning(request, "退会済みユーザーは操作できません。")
        return _redirect_admins()
    if target == request.user:
        messages.warning(request, "自分自身の is_keeper は変更できません。")
        return _redirect_admins()
    if not hasattr(target, "is_keeper"):
        messages.error(request, "このユーザーには is_keeper フィールドがありません。")
        return _redirect_admins()

    target.is_keeper = not target.is_keeper
    target.save(update_fields=["is_keeper"])
    messages.success(request, f"{target.username} の is_keeper を {target.is_keeper} に変更しました。")
    return _redirect_admins()


@require_POST
@staff_required
def toggle_superuser(request: HttpRequest, pk: int) -> HttpResponse:
    """
    is_superuser の ON/OFF
    - 操作者: superuser のみ許可
    - 対象: 自分は不可
    - superuser を付与する場合は is_staff も True にして整合性を取る
    - 退会済み（is_active=False）は操作不可
    """
    if not _must_superuser(request):
        return _redirect_admins()

    target = get_object_or_404(User, pk=pk)
    if not target.is_active:
        messages.warning(request, "退会済みユーザーは操作できません。")
        return _redirect_admins()
    if target == request.user:
        messages.warning(request, "自分自身の superuser はここでは変更できません。")
        return _redirect_admins()

    target.is_superuser = not target.is_superuser
    if target.is_superuser and not target.is_staff:
        target.is_staff = True
        target.save(update_fields=["is_superuser", "is_staff"])
    else:
        target.save(update_fields=["is_superuser"])

    messages.success(request, f"{target.username} の is_superuser を {target.is_superuser} に変更しました。")
    return _redirect_admins()


# ==============================================
# 退会（削除の代替：is_active=False + セッション失効）
# ==============================================
@require_POST
@staff_required
def withdraw_user(request: HttpRequest, pk: int) -> HttpResponse:
    if not _must_superuser(request):
        return _redirect_admins()

    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.warning(request, "自分自身は退会できません。")
        return _redirect_admins()
    if target.is_superuser:
        messages.warning(request, "superuser は退会できません。")
        return _redirect_admins()

    # 退会は is_active=False のみ（権限は保持）
    if target.is_active:
        target.is_active = False
        target.save(update_fields=["is_active"])

    # セッション失効
    for s in Session.objects.filter(expire_date__gt=timezone.now()):
        data = s.get_decoded()
        if data.get("_auth_user_id") == str(target.pk):
            s.delete()

    messages.success(request, f"{target.username} を退会処理しました（ログイン不可）。")
    return _redirect_admins()



# ==============================================
# 退会解除（再開）
# ==============================================
@require_POST
@staff_required
def reactivate_user(request: HttpRequest, pk: int) -> HttpResponse:
    """
    退会解除（再開）
    - 操作者: superuser のみ
    - デフォルトでは is_active=True のみ復活（is_staff 付与は別操作）
    """
    if not _must_superuser(request):
        return _redirect_admins()

    target = get_object_or_404(User, pk=pk)
    if target == request.user:
        messages.warning(request, "自分自身の再開はここでは行えません。")
        return _redirect_admins()

    if target.is_active:
        messages.info(request, f"{target.username} は既に有効です。")
        return _redirect_admins()

    target.is_active = True
    target.save(update_fields=["is_active"])

    messages.success(request, f"{target.username} を再開しました（ログイン可）。")
    return _redirect_admins()


# ==============================================
# is_staff 新規登録（superuser のみ）
# ==============================================
from .forms import StaffCreateForm

class StaffCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "dashboard/staff_create.html"
    form_class = StaffCreateForm
    success_url = reverse_lazy("dashboard:admins_list")

    def test_func(self):
        # 作成できるのは superuser のみ（要件）
        return self.request.user.is_superuser

    def form_valid(self, form):
        new_user = form.save()
        messages.success(self.request, f"管理者ユーザー「{new_user.username}」を作成しました。")
        return super().form_valid(form)


# dashboard/views.py の末尾あたりに追加
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from .forms import StaffEditForm

class StaffUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = StaffEditForm
    template_name = "dashboard/admin_edit.html"
    context_object_name = "target_user"
    success_url = reverse_lazy("dashboard:admins_list")

    # 権限チェック：superuserは誰でもOK、staffは自分だけ
    def test_func(self):
        me = self.request.user
        target = self.get_object()

        # superuser は誰でも編集可（※superuser相手でもOK）
        if me.is_superuser:
            return True

        # staff なら「自分」だけ編集可
        if me.is_staff and me.pk == target.pk:
            return True

        return False

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, f"「{self.object.username}」の情報を更新しました。")
        return resp
