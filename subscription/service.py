# subscription/service.py

from datetime import date, timedelta
from django.db import transaction

from subscription.models import SubMember, _add_months
from money.models import Wallet


def run_monthly_subscription_update():
    """
    継続サブスク（月額プラン）の更新処理。

    対象:
      - is_active=True  … 有効な契約
      - is_recurring=True … 継続プラン
      - end_day < 今日  … 期限が過ぎている契約

    処理内容:
      - 契約終了日(end_day)を1ヶ月延長
      - sign_mon（通算継続月数）を +1
      - 会員ウォレットにスタポ(plan.st_point)を付与
      - 動物の所属Zooにサブスク金額(plan.amount)を加算
    """
    today = date.today()

    subs = (
        SubMember.objects
        .select_related("member", "plan", "animal__zoo")
        .filter(
            is_active=True,
            is_recurring=True,
            end_day__isnull=False,
            end_day__lt=today,   # ← 今日より前に切れている契約だけ更新
        )
    )

    total_subs = subs.count()
    updated = 0
    total_points = 0
    total_amount = 0
    skipped_no_zoo = 0

    for sub in subs:
        member = sub.member
        plan = sub.plan
        zoo = sub.animal.zoo

        # Zoo が設定されていない場合はスキップ
        if not zoo:
            skipped_no_zoo += 1
            continue

        add_point = plan.st_point or 0   # 付与するスタポ
        add_amount = plan.amount or 0    # Zoo に積み上げる金額

        with transaction.atomic():
            # ① 契約期間を1ヶ月延長
            start = sub.end_day + timedelta(days=1)
            new_end = _add_months(start, 1) - timedelta(days=1)
            sub.end_day = new_end
            sub.sign_mon = (sub.sign_mon or 0) + 1
            sub.save(update_fields=["end_day", "sign_mon"])

            # ② ウォレットにスタポ付与
            if add_point > 0:
                wallet, _ = Wallet.objects.select_for_update().get_or_create(member=member)
                wallet.stanning_point_balance = (wallet.stanning_point_balance or 0) + add_point
                wallet.save(update_fields=["stanning_point_balance"])
                total_points += add_point

            # ③ Zoo にサブスク金額を加算
            if add_amount > 0:
                zoo.sub_unpaid_amount = (zoo.sub_unpaid_amount or 0) + add_amount
                zoo.save(update_fields=["sub_unpaid_amount"])
                total_amount += add_amount

            updated += 1

    return {
        "total_subscriptions": total_subs,
        "updated": updated,
        "skipped_no_zoo": skipped_no_zoo,
        "total_points_added": total_points,
        "total_amount_added": total_amount,
    }
