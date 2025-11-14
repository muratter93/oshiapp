from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponse
from subscription.service import grant_plan_points_to_wallet
from subscription.models import SubscribePlan

@login_required
def purchase_done(request, code: str):
    """
    購入完了想定の超シンプルなビュー。
    /subscription/buy/<code>/done/ を叩くと、スタポを付与してサンクスを返す。
    """
    plan = get_object_or_404(SubscribePlan, code=code)
    new_balance = grant_plan_points_to_wallet(request.user, plan.code)
    return HttpResponse(f"{plan.code} を付与しました。残高: {new_balance}")


# 推しプラン
# subscription/views.py
from django.shortcuts import render, get_object_or_404
from animals.models import Animal
from .models import SubscribePlan

def plan_list_by_animal(request, animal_id: int):
    animal = get_object_or_404(Animal, pk=animal_id)
    plans = SubscribePlan.objects.all()  # 今は全プラン表示
    return render(request, "subscription/plan_list.html", {
        "animal": animal,
        "plans": plans
    })


from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from .models import SubscribePlan, SubMember
from animals.models import Animal

@login_required
def confirm_plan(request, plan_id, animal_id):
    animal = get_object_or_404(Animal, pk=animal_id)
    plan = get_object_or_404(SubscribePlan, pk=plan_id)
    return render(request, "subscription/confirm_plan.html", {
        "animal": animal,
        "plan": plan
    })

@login_required
def join_plan(request, plan_id, animal_id):
    animal = get_object_or_404(Animal, pk=animal_id)
    plan = get_object_or_404(SubscribePlan, pk=plan_id)

    # 現在有効なプランがこの動物にあるか確認
    existing_active = SubMember.objects.filter(
        member=request.user,
        animal=animal,
        is_active=True
    ).first()

    if existing_active:
        # 有効プランがある場合は加入できない
        return render(request, "subscription/join_done.html", {
            "animal": animal,
            "plan": plan,
            "error": f"すでに {animal.japanese} に有効な加入プランがあります（プラン: {existing_active.plan.plan_name}）"
        })

    # ① 新規加入
    sub = SubMember.objects.create(member=request.user, plan=plan, animal=animal)

    # ⭐ ② 加入した瞬間にスタポ付与！（これを追加する）
    from subscription.service import grant_plan_points_to_wallet
    grant_plan_points_to_wallet(request.user, plan.code)

    # 完了ポップアップ + 詳細に戻る
    return render(request, "subscription/join_done.html", {
        "animal": animal,
        "plan": plan
    })




# バルス
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect
from django.db import connection
from subscription.models import SubMember

@staff_member_required  # 管理者だけ実行可
def reset_sub_members(request):
    """
    SubMember テーブルを空にしてIDを1からリセット。
    SubscribePlan は削除しません。
    """
    # テーブルを削除
    SubMember.objects.all().delete()

    # SQLite / MySQL / PostgreSQL に合わせてリセット
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


# サブスク解約
@login_required
def cancel_subscription(request, sub_member_id):
    """
    サブスク解約処理
    """
    sub = get_object_or_404(SubMember, pk=sub_member_id, member=request.user, is_recurring=True)

    if request.method == "POST":
        # 解約処理
        sub.is_active = False
        sub.save(update_fields=["is_active"])
        # 完了画面ではなく履歴ページに戻す
        return redirect("money:purchase_history")

    # GETで来た場合は確認ページ
    return redirect("money:purchase_history")




@login_required
def cancel_done(request, sub_member_id):
    sub = get_object_or_404(SubMember, pk=sub_member_id, member=request.user)
    return render(request, "money/cancel_done.html", {"sub": sub})
