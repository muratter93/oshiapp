from datetime import date, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db import transaction, connection
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect

from animals.models import Animal, Zoo
from money.models import Wallet
from .models import SubscribePlan, SubMember, _add_months

from django.contrib import messages

# ---------------- 購入完了（※ここでは付与処理はしない想定） ----------------

@login_required
def purchase_done(request, code: str):
    """
    購入完了画面。
    ※スタポ付与やZoo加算は別のロジック/コマンドで行う前提。
    """
    plan = get_object_or_404(SubscribePlan, code=code)
    return HttpResponse(f"{plan.code} の購入が完了しました。")


# ---------------- プラン一覧（動物別） ----------------

def plan_list_by_animal(request, animal_id: int):
    animal = get_object_or_404(Animal, pk=animal_id)
    plans = SubscribePlan.objects.all()  # 今は全プラン表示
    return render(request, "subscription/plan_list.html", {
        "animal": animal,
        "plans": plans,
    })


# ---------------- プラン確認／加入 ----------------

@login_required
def confirm_plan(request, plan_id, animal_id):
    animal = get_object_or_404(Animal, pk=animal_id)
    plan = get_object_or_404(SubscribePlan, pk=plan_id)
    return render(request, "subscription/confirm_plan.html", {
        "animal": animal,
        "plan": plan,
    })


@login_required
@transaction.atomic
def join_plan(request, plan_id, animal_id):
    """
    サブスク加入処理。

    やること：
      1. SubMember を新規作成
      2. 加入した瞬間に、
         - 会員ウォレットにスタポ(plan.st_point)を加算
         - 動物の所属Zooにサブスク金額(plan.amount)を加算
    """
    animal = get_object_or_404(Animal, pk=animal_id)
    plan = get_object_or_404(SubscribePlan, pk=plan_id)

    # すでにこの動物に対して有効なプランがあるか？（重複加入の防止）
    existing_active = SubMember.objects.filter(
        member=request.user,
        animal=animal,
        is_active=True,
    ).first()

    if existing_active:
        return render(request, "subscription/join_done.html", {
            "animal": animal,
            "plan": plan,
            "error": f"すでに {animal.name} に有効な加入プランがあります（プラン: {existing_active.plan.plan_name}）",
        })

    # ① 新規加入レコードを作成
    SubMember.objects.create(member=request.user, plan=plan, animal=animal)

    # ② 加入時スタポ付与 ＋ Zoo に初回分サブスク金額加算
    add_point = plan.st_point or 0
    add_amount = plan.amount or 0

    # ②-1 ウォレット（スタポ）
    if add_point > 0:
        wallet, _ = Wallet.objects.select_for_update().get_or_create(member=request.user)
        wallet.stanning_point_balance = (wallet.stanning_point_balance or 0) + add_point
        wallet.save(update_fields=["stanning_point_balance"])

    # ②-2 Zoo（未支援サブスク累計額）
    zoo = animal.zoo
    if zoo and add_amount > 0:
        zoo.sub_unpaid_amount = (zoo.sub_unpaid_amount or 0) + add_amount
        zoo.save(update_fields=["sub_unpaid_amount"])

    # 完了画面へ
    return render(request, "subscription/join_done.html", {
        "animal": animal,
        "plan": plan,
    })


# ---------------- SubMember リセット（開発用） ----------------

@staff_member_required  # 管理者だけ実行可
def reset_sub_members(request):
    """
    SubMember テーブルを空にしてIDを1からリセット。
    SubscribePlan は削除しません。
    """
    # テーブルを削除
    SubMember.objects.all().delete()

    # SQLite / MySQL / PostgreSQL に合わせてIDリセット
    table_name = SubMember._meta.db_table
    engine = connection.vendor

    if engine == "sqlite":
        # SQLite は sqlite_sequence をリセット
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")
    elif engine == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER SEQUENCE {table_name}_sub_member_id_seq RESTART WITH 1")
    elif engine == "mysql":
        with connection.cursor() as cursor:
            cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1")
    else:
        pass  # 他のDBは必要に応じて

    # 完了したら管理画面に戻す
    return redirect("/admin/")


# ---------------- サブスク解約 ----------------

@login_required
def cancel_subscription(request, sub_member_id):
    """
    サブスク解約処理
    """
    sub = get_object_or_404(
        SubMember,
        pk=sub_member_id,
        member=request.user,
        is_recurring=True,
    )

    if request.method == "POST":
        # 解約処理
        sub.is_active = False
        sub.save(update_fields=["is_active"])

        # ★ これを追加
        messages.success(request, " 〇〇さんの〜プランのサブスクが解約されました。")

        # 履歴ページに戻す
        return redirect("money:purchase_history2")

    # GETで来た場合は、とりあえず履歴に戻す
    return redirect("money:purchase_history2")


@login_required
def cancel_done(request, sub_member_id):
    sub = get_object_or_404(SubMember, pk=sub_member_id, member=request.user)
    return render(request, "money/cancel_done.html", {"sub": sub})


# ---------------- （オプション）ビューから実行するサブスク更新 ----------------
# ※ 継続分は基本「管理コマンド + service」でやる想定なので、
#   これは admin からテストしたいとき用。不要なら消してもOK。

@staff_member_required
@transaction.atomic
def run_subscription_billing(request):
    """
    （管理画面から叩く用）サブスク更新処理:
    - is_active=True & is_recurring=True & end_day < 今日 を1ヶ月延長
    - Zoo にサブスク金額を加算
    ※ ウォレットへのスタポ付与は、必要なら管理コマンドやservice側で行う想定。
    """
    today = date.today()

    subs = SubMember.objects.select_related("plan", "animal__zoo").filter(
        is_active=True,
        is_recurring=True,
        end_day__lt=today,
    )

    count = 0

    for sub in subs:
        # 1ヶ月延長
        new_end = _add_months(sub.end_day + timedelta(days=1), 1) - timedelta(days=1)
        sub.end_day = new_end
        sub.sign_mon += 1
        sub.save(update_fields=["end_day", "sign_mon"])

        # 動物園にサブスク料金を追加
        zoo = sub.animal.zoo
        if zoo:
            zoo.sub_unpaid_amount = (zoo.sub_unpaid_amount or 0) + sub.plan.amount
            zoo.save(update_fields=["sub_unpaid_amount"])

        count += 1

    return HttpResponse(f"サブスク更新処理完了：{count} 件更新されました")
