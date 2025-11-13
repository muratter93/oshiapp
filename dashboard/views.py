from functools import wraps
from typing import Callable

from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, FormView, UpdateView

from django.utils import timezone
from django.contrib.sessions.models import Session

from .forms import StaffCreateForm, StaffEditForm, KeeperCreateForm, KeeperEditForm, AnimalForm 

User = get_user_model()

# ---------------- 認可ヘルパ ----------------

def is_staff_or_keeper(u) -> bool:
    """staff / keeper / superuser のいずれかなら True"""
    return bool(getattr(u, "is_superuser", False)
                or getattr(u, "is_staff", False)
                or getattr(u, "is_keeper", False))


def staff_required(view_func: Callable) -> Callable:
    """従来どおり staff（または superuser）だけを通すデコレータ。操作系で使用。"""
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


def staff_or_keeper_required(view_func: Callable) -> Callable:
    """ダッシュボードの閲覧入口用: staff か keeper で通す。"""
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = request.user
        if not user.is_authenticated:
            login_url = f"{reverse('dashboard:dashboard_login')}?next={request.get_full_path()}"
            return redirect(login_url)
        if not is_staff_or_keeper(user):
            return redirect('dashboard:dashboard_error')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ---------------- 画面 ----------------
@staff_or_keeper_required
def admin_dashboard(request: HttpRequest) -> HttpResponse:
    return render(request, "dashboard/dashboard.html")


def access_denied(request: HttpRequest) -> HttpResponse:
    return render(request, "dashboard/dashboard_error.html")


class DashboardLoginView(LoginView):
    template_name = "dashboard/dashboard_login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        # staff だけでなく keeper も許可
        if is_staff_or_keeper(self.request.user):
            return self.get_redirect_url() or reverse("dashboard:dashboard")
        # 権限なしユーザーが来た場合はエラーへ
        return reverse("dashboard:dashboard_error")


# ---------------- 一覧（管理者＋飼育員 閲覧可） ----------------
class StaffListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = "dashboard/admins_list.html"
    context_object_name = "users"
    paginate_by = 10

    def test_func(self):
        return is_staff_or_keeper(self.request.user)

    def _admin_base_q(self):
        field_names = {f.name for f in User._meta.get_fields()}
        if "is_keeper" in field_names:
            return User.objects.filter(Q(is_staff=True) | Q(is_keeper=True))
        return User.objects.filter(is_staff=True)

    def get_queryset(self):
        base = self._admin_base_q()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            base = base.filter(Q(username__icontains=q) | Q(email__icontains=q))

        status = (self.request.GET.get("status") or "all").strip()
        if status == "active":
            base = base.filter(is_active=True)
        elif status == "inactive":
            base = base.filter(is_active=False)

        order = (self.request.GET.get("order") or "-id").strip()
        allowed = {"id", "-id", "username", "-username", "email", "-email", "last_login", "-last_login"}
        if order not in allowed:
            order = "-id"

        return base.order_by(order)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        base_all = self._admin_base_q()
        ctx.update({
            "q": (self.request.GET.get("q") or "").strip(),
            "order": (self.request.GET.get("order") or "-id").strip(),
            "status": (self.request.GET.get("status") or "all").strip(),
            "counts": {
                "all": base_all.count(),
                "active": base_all.filter(is_active=True).count(),
                "inactive": base_all.filter(is_active=False).count(),
            },
        })
        return ctx

# ---------------- 権限トグル＆退会関連（操作系: staff/superuser のみ） ----------------

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
    if target.is_active:
        target.is_active = False
        target.save(update_fields=["is_active"])
    for s in Session.objects.filter(expire_date__gt=timezone.now()):
        data = s.get_decoded()
        if data.get("_auth_user_id") == str(target.pk):
            s.delete()
    messages.success(request, f"{target.username} を退会処理しました（ログイン不可）。")
    return _redirect_admins()


@require_POST
@staff_required
def reactivate_user(request: HttpRequest, pk: int) -> HttpResponse:
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


# ---------------- 作成/編集画面 ----------------
class StaffCreateView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "dashboard/staff_create.html"
    form_class = StaffCreateForm
    success_url = reverse_lazy("dashboard:admins_list")

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        new_user = form.save()
        messages.success(self.request, f"管理者ユーザー「{new_user.username}」を作成しました。")
        return super().form_valid(form)


@login_required
@user_passes_test(lambda u: u.is_superuser or u.is_staff)
def keeper_create(request):
    if request.method == "POST":
        form = KeeperCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"飼育員ユーザー「{user.username}」を作成しました。")
            return redirect("dashboard:admins_list")
    else:
        form = KeeperCreateForm()
    return render(request, "dashboard/keeper_create.html", {"form": form})


class StaffUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = StaffEditForm
    template_name = "dashboard/admin_edit.html"
    context_object_name = "target_user"
    success_url = reverse_lazy("dashboard:admins_list")

    def test_func(self):
        me = self.request.user
        target = self.get_object()
        if me.is_superuser:
            return True
        return me.is_staff and me.pk == target.pk

    def form_valid(self, form):
        resp = super().form_valid(form)
        messages.success(self.request, f"「{self.object.username}」の情報を更新しました。")
        return resp


class MemberListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "dashboard/members_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        qs = User.objects.filter(is_staff=False, is_superuser=False)
        if hasattr(User, "is_keeper"):
            qs = qs.filter(is_keeper=False)
        return qs.order_by("-id")


class MemberUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    fields = ["username", "name", "email", "birth", "postal_code", "address", "phone"]
    template_name = "dashboard/member_edit.html"
    context_object_name = "member"
    success_url = reverse_lazy("dashboard:member_list")

    def test_func(self):
        u = self.request.user
        obj = self.get_object()
        return u.is_superuser or u.is_staff or (u == obj)

    def form_valid(self, form):
        messages.success(self.request, "会員情報を更新しました。")
        return super().form_valid(form)

    def handle_no_permission(self):
        messages.error(self.request, "権限がありません。")
        return redirect("dashboard:member_list")


class KeeperUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = KeeperEditForm
    template_name = "dashboard/keeper_edit.html"
    context_object_name = "target_user"
    success_url = reverse_lazy("dashboard:admins_list")

    # 権限は管理者側と同じでOK（superuser / staff に許可）
    def test_func(self):
        u = self.request.user
        return u.is_superuser or u.is_staff

    def form_valid(self, form):
        messages.success(self.request, f"飼育員「{self.object.username}」の情報を更新しました。")
        return super().form_valid(form)


# 退会/再開（一般会員用）
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
@require_POST
def withdraw_member(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = False
    user.save()
    messages.warning(request, f"{user.username} を退会処理しました。")
    return redirect("dashboard:member_list")


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
@require_POST
def reactivate_member(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.is_active = True
    user.save()
    messages.success(request, f"{user.username} を再開しました。")
    return redirect("dashboard:member_list")


from animals.models import Animal, Zoo
from django.core.paginator import Paginator

@staff_or_keeper_required
def animals_list(request):
    user = request.user
    qs = Animal.objects.select_related("zoo")

    # --- keeper専用スコープ（staff/superuser ではない）---
    if getattr(user, "is_keeper", False) and not (user.is_staff or user.is_superuser):

        if getattr(user, "zoo_id", None):
            qs = qs.filter(zoo_id=user.zoo_id)
        else:
            qs = qs.none()

    qs = qs.order_by("-animal_id")

    # --- ページネーション（10件ずつ）---
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "dashboard/animals_list.html",
        {
            "animals": page_obj,   # そのままループに使える
            "page_obj": page_obj,
            "paginator": paginator,
        }
    )

# 追加：動物登録
@staff_or_keeper_required
def animal_create(request):
    form = AnimalForm(
        request.POST or None,
        request.FILES or None,
        user=request.user,   # ← 追加
    )
    if request.method == "POST" and form.is_valid():
        animal = form.save(commit=False)

        if getattr(request.user, "is_keeper", False) and request.user.zoo_id:
            animal.zoo = request.user.zoo

        animal.save()
        messages.success(request, f"「{animal.japanese}（{animal.name}）」を登録しました。")
        return redirect("dashboard:animals_list")

    return render(request, "dashboard/animal_create.html", {"form": form, "mode": "create"})

# 追加：動物編集
@staff_or_keeper_required
def animal_edit(request, pk: int):
    animal = get_object_or_404(Animal, pk=pk)

    form = AnimalForm(
        request.POST or None,
        request.FILES or None,
        instance=animal,
        user=request.user,   # ← ここ追加！
    )

    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)

        # ★ keeper の場合は zoo を自分の所属動物園に固定
        if getattr(request.user, "is_keeper", False) and request.user.zoo_id:
            obj.zoo = request.user.zoo

        obj.save()
        messages.success(request, "動物情報を更新しました。")
        return redirect("dashboard:animals_list")

    return render(
        request,
        "dashboard/animal_edit.html",
        {"form": form, "mode": "edit", "animal": animal},
    )

@require_POST
@staff_or_keeper_required
def animal_withdraw(request, pk: int):
    animal = get_object_or_404(Animal, pk=pk)
    if not animal.is_active:
        messages.info(request, f"「{animal.japanese}（{animal.name}）」は既に休止中です。")
        return redirect("dashboard:animals_list")
    animal.is_active = False
    animal.save(update_fields=["is_active"])
    messages.warning(request, f"「{animal.japanese}（{animal.name}）」を休止にしました。")
    return redirect("dashboard:animals_list")

@require_POST
@staff_or_keeper_required
def animal_reactivate(request, pk: int):
    animal = get_object_or_404(Animal, pk=pk)
    if animal.is_active:
        messages.info(request, f"「{animal.japanese}（{animal.name}）」は既に有効です。")
        return redirect("dashboard:animals_list")
    animal.is_active = True
    animal.save(update_fields=["is_active"])
    messages.success(request, f"「{animal.japanese}（{animal.name}）」を再開しました。")
    return redirect("dashboard:animals_list")

