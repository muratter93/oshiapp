from functools import wraps
from typing import Callable

from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, FormView, UpdateView
from subscription.models import SubMember

from django.utils import timezone
from django.contrib.sessions.models import Session

from .forms import StaffCreateForm, StaffEditForm, KeeperCreateForm, KeeperEditForm, AnimalForm, GiftForm

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
    user = request.user

    # ベース：全 Zoo
    zoo_qs = Zoo.objects.all()

    # keeper は自分の動物園だけ（staff/superuser は全体）
    if getattr(user, "is_keeper", False) and not (user.is_staff or user.is_superuser):
        if getattr(user, "zoo_id", None):
            zoo_qs = zoo_qs.filter(pk=user.zoo_id)
        else:
            zoo_qs = zoo_qs.none()

    # ★ Zoo ごとの「累計動物推しポイント」だけ annotate
    zoo_qs = zoo_qs.annotate(
        total_point_sum=Coalesce(Sum("animals__total_point"), 0),
    ).order_by("zoo_id")

    total_points_all_zoo = 0
    total_unpaid_points = 0
    total_unpaid_coins = 0

    total_sub_all_zoo = 0
    total_unpaid_sub_all = 0

    for zoo in zoo_qs:
        # --- ポイント系 ---
        total_points_all_zoo += zoo.total_point_sum

        base_pt = zoo.last_paid_point_sum or 0
        unpaid_pt = max(zoo.total_point_sum - base_pt, 0)
        coins = unpaid_pt * 80

        zoo.unpaid_points = unpaid_pt
        zoo.unpaid_coins = coins

        total_unpaid_points += unpaid_pt
        total_unpaid_coins += coins

        # --- サブスク系：ここだけ SubMember から素直に集計する ---
        sub_agg = SubMember.objects.filter(
            animal__zoo=zoo,
            is_active=True,   # 今有効なサブスクだけカウント
        ).aggregate(total=Coalesce(Sum("plan__amount"), 0))

        sub_total = sub_agg["total"] or 0
        zoo.sub_total_sum = sub_total  # 累計サブスク金額（v1）

        base_sub = zoo.last_paid_sub_total or 0
        unpaid_sub = max(sub_total - base_sub, 0)

        zoo.unpaid_sub_amount = unpaid_sub  # 今回サブスク支援額（円）

        zoo.sub_paid_total = zoo.last_paid_sub_total

        total_sub_all_zoo += sub_total
        total_unpaid_sub_all += unpaid_sub

    context = {
        "zoo_points": zoo_qs,

        # ポイント系サマリ
        "total_points_all_zoo": total_points_all_zoo,
        "total_unpaid_points": total_unpaid_points,
        "total_unpaid_coins": total_unpaid_coins,

        # サブスク系サマリ
        "total_sub_all_zoo": total_sub_all_zoo,
        "total_unpaid_sub_all": total_unpaid_sub_all,
    }
    return render(request, "dashboard/dashboard.html", context)



def access_denied(request: HttpRequest) -> HttpResponse:
    return render(request, "dashboard/dashboard_error.html")

@require_POST
@staff_required
def zoo_payout(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Zoo ごとの「未支援ポイント」を支援確定する。
    差分ポイントを支援済みとして扱い、last_paid_point_sum / last_paid_at を更新。
    """
    zoo = get_object_or_404(Zoo, pk=pk)

    # 現時点の累計ポイントを再集計（念のためその場で計算）
    agg = zoo.animals.aggregate(
        total_point_sum=Coalesce(Sum("total_point"), 0)
    )
    total_point_sum = agg["total_point_sum"] or 0

    base = zoo.last_paid_point_sum or 0
    unpaid_points = max(total_point_sum - base, 0)

    if unpaid_points <= 0:
        messages.info(request, f"{zoo.zoo_name} には未支援ポイントがありません。")
        return redirect("dashboard:dashboard")

    coins = unpaid_points * 100

    # ここで本当は「支援履歴テーブル」にもレコードを切るのがベストだが、
    # v1 では Zoo 側の基準値だけ更新する。
    zoo.last_paid_point_sum = total_point_sum
    zoo.last_paid_at = timezone.now()
    zoo.save(update_fields=["last_paid_point_sum", "last_paid_at"])

    messages.success(
        request,
        f"{zoo.zoo_name} に {unpaid_points:,}pt（{coins:,}コイン）分の支援を確定しました。",
    )
    return redirect("dashboard:dashboard")


@require_POST
@staff_required
def zoo_sub_payout(request: HttpRequest, pk: int) -> HttpResponse:
    """
    動物園の未支援サブスク金額を支援確定する。
    - sub_unpaid_amount → last_paid_sub_total に加算
    - sub_unpaid_amount を 0 にリセット
    """
    zoo = get_object_or_404(Zoo, pk=pk)

    unpaid = zoo.sub_unpaid_amount

    if unpaid <= 0:
        messages.info(request, f"{zoo.zoo_name} に未支援サブスクはありません。")
        return redirect("dashboard:dashboard")

    # ★ 累計に加算（last_paid_sub_total は累計版として再利用）
    zoo.last_paid_sub_total += unpaid

    # ★ 今回分をゼロにする（リセット）
    zoo.sub_unpaid_amount = 0

    # ★ 支援日時を更新
    zoo.last_paid_sub_at = timezone.now()

    zoo.save(update_fields=[
        "last_paid_sub_total",
        "sub_unpaid_amount",
        "last_paid_sub_at"
    ])

    messages.success(
        request,
        f"{zoo.zoo_name} にサブスク {unpaid:,} 円の支援を確定しました！"
    )
    return redirect("dashboard:dashboard")


class DashboardLoginView(LoginView):
    template_name = "dashboard/dashboard_login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        # staff だけでなく keeper も許可
        if is_staff_or_keeper(self.request.user):
            return self.get_redirect_url() or reverse("dashboard:dashboard")
        # 権限なしユーザーが来た場合はエラーへ
        return reverse("dashboard:dashboard_error")
    
class DashboardLoginView(LoginView):
    template_name = "dashboard/dashboard_login.html"
    redirect_authenticated_user = True

    def get_success_url(self) -> str:
        # staff だけでなく keeper も許可
        if is_staff_or_keeper(self.request.user):
            return self.get_redirect_url() or reverse("dashboard:dashboard")
        # 権限なしユーザーが来た場合はエラーへ
        return reverse("dashboard:dashboard_error")

@login_required
def dashboard_logout(request: HttpRequest) -> HttpResponse:
    """ダッシュボード用ログアウト"""
    logout(request)
    messages.info(request, "ログアウトしました。")
    return redirect("dashboard:dashboard_login")



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
from django.shortcuts import render

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

    # --- フィルタ条件 ---
    zoo_id = request.GET.get("zoo")      # ?zoo=3 みたいなやつ
    order  = request.GET.get("order")    # ?order=point_desc など

    # 動物園フィルタ
    if zoo_id:
        qs = qs.filter(zoo_id=zoo_id)

    # 並び順
    if order == "point_desc":
        qs = qs.order_by("-total_point", "-animal_id")
    elif order == "id_asc":
        qs = qs.order_by("animal_id")                 # ← 昇順
    else:
        qs = qs.order_by("-animal_id")                # ← 降順（デフォルト）

    # --- ページネーション（10件ずつ）---
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "dashboard/animals_list.html",
        {
            "animals": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
            "zoos": Zoo.objects.all().order_by("zoo_name"),  # ボタン用
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



from datetime import date
from django.shortcuts import redirect
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from subscription.models import SubMember


class SubscriptionListView(LoginRequiredMixin, ListView):
    model = SubMember
    template_name = "dashboard/subscription_list.html"
    context_object_name = "subs"
    paginate_by = 50

    def get_queryset(self):
        qs = (
            SubMember.objects
            .select_related("member", "plan", "animal")
            .order_by("-sign_up", "-sub_member_id")
        )

        # キーワード検索（後で拡張可能）
        q = self.request.GET.get("q") or ""
        if q:
            qs = qs.filter(member__username__icontains=q)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["today"] = date.today()
        ctx["q"] = self.request.GET.get("q") or ""
        return ctx


from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from subscription.models import SubMember   # ★ モデル名はこれ


def sub_cancel(request, sub_member_id):
    sub = get_object_or_404(SubMember, pk=sub_member_id)

    if request.method == "POST":
        today = timezone.localdate()

        # 解約処理
        sub.end_day = today
        sub.is_recurring = False   # 継続フラグOFF
        sub.is_active = False      # ★ ステータスを「終了」に
        sub.save()

    return redirect("dashboard:subscription_list")


def sub_restart(request, sub_member_id):
    sub = get_object_or_404(SubMember, pk=sub_member_id)

    if request.method == "POST":
        today = timezone.localdate()

        # 再開処理
        sub.sign_up = today        # 再開日を新しい加入日に
        sub.end_day = None         # 終了日クリア（save内で再計算するならこのまま）
        sub.is_recurring = True    # 継続ON（不要なら外してOK）
        sub.is_active = True       # ★ ステータスを「有効」に
        sub.save()

    return redirect("dashboard:subscription_list")


from django.shortcuts import render
from gift.models import Gift

# --------------------------------
# 返礼品（Gift） 管理
# --------------------------------

from django.core.paginator import Paginator

@staff_or_keeper_required
def gift_list(request: HttpRequest) -> HttpResponse:
    """返礼品一覧"""
    user = request.user
    qs = Gift.objects.select_related("zoo")

    # keeper は自分の動物園だけ
    if getattr(user, "is_keeper", False) and not (user.is_staff or user.is_superuser):
        if getattr(user, "zoo_id", None):
            qs = qs.filter(zoo_id=user.zoo_id)
        else:
            qs = qs.none()

    qs = qs.order_by("-id")  # 新しい順

    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "dashboard/gift_list.html",
        {
            "gifts": page_obj,
            "page_obj": page_obj,
            "paginator": paginator,
        },
    )


@staff_or_keeper_required
def gift_create(request: HttpRequest) -> HttpResponse:
    """返礼品 新規登録"""
    form = GiftForm(
        request.POST or None,
        request.FILES or None,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        gift = form.save(commit=False)

        # keeper の場合は所属動物園を自分の zoo に固定（保険）
        if getattr(request.user, "is_keeper", False) and getattr(request.user, "zoo_id", None):
            gift.zoo = request.user.zoo

        gift.save()
        messages.success(request, f"返礼品「{gift.title}」を登録しました。")
        return redirect("dashboard:gift_list")

    return render(
        request,
        "dashboard/gift_create.html",
        {"form": form, "mode": "create"},
    )


@staff_or_keeper_required
def gift_edit(request: HttpRequest, pk: int) -> HttpResponse:
    """返礼品 編集"""
    gift = get_object_or_404(Gift, pk=pk)

    form = GiftForm(
        request.POST or None,
        request.FILES or None,
        instance=gift,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)

        # keeper の場合は zoo を自分に固定
        if getattr(request.user, "is_keeper", False) and getattr(request.user, "zoo_id", None):
            obj.zoo = request.user.zoo

        obj.save()
        messages.success(request, f"返礼品「{obj.title}」の情報を更新しました。")
        return redirect("dashboard:gift_list")

    return render(
        request,
        "dashboard/gift_edit.html",
        {"form": form, "gift": gift, "mode": "edit"},
    )


@require_POST
@staff_or_keeper_required
def gift_delete(request: HttpRequest, pk: int) -> HttpResponse:
    """返礼品 削除（物理削除）"""
    gift = get_object_or_404(Gift, pk=pk)
    title = gift.title
    gift.delete()
    messages.error(request, f"返礼品「{title}」を削除しました。")
    return redirect("dashboard:gift_list")

# サブスク会員詳細ページに
from django.views.generic import DetailView
from accounts.models import Member
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin

class MemberDetailView(LoginRequiredMixin, DetailView):
    model = Member
    template_name = "dashboard/subscription_member_detail.html"
    context_object_name = "member"

    def get_object(self, queryset=None):
        member = super().get_object(queryset)

        # --- keeper（動物園管理人）の場合は所属で閲覧制限 ---
        if self.request.user.is_keeper:
            if member.zoo != self.request.user.zoo:
                raise PermissionError("この会員情報にはアクセスできません。")

        return member