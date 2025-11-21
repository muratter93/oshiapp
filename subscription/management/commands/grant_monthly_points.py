from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from django.utils import timezone

from subscription.models import SubMember, _add_months
from money.models import Wallet


class Command(BaseCommand):
    help = '継続プランの会員に毎月スタポを付与し、終了日を次の月に延長し、Zoo にサブスク金額を加算します'

    def handle(self, *args, **options):

        today = date.today()

        # end_day < 今日 の契約が「更新対象」
        subs = (
            SubMember.objects
            .select_related("member", "plan", "animal__zoo")
            .filter(
                is_recurring=True,
                is_active=True,
                end_day__isnull=False,
                end_day__lt=today,
            )
        )

        total = subs.count()
        updated = 0
        total_points = 0
        total_amount = 0
        skipped_no_zoo = 0

        for sub in subs:
            plan = sub.plan
            zoo = sub.animal.zoo

            if not zoo:
                skipped_no_zoo += 1
                continue

            add_point = plan.st_point or 0
            add_amount = plan.amount or 0

            with transaction.atomic():
                # --- ① スタポ付与 ---
                if add_point > 0:
                    wallet, _ = Wallet.objects.select_for_update().get_or_create(member=sub.member)
                    wallet.stanning_point_balance += add_point
                    wallet.save(update_fields=["stanning_point_balance"])
                    total_points += add_point

                # --- ② Zoo の未支援サブスク額を加算 ---
                zoo.sub_unpaid_amount = (zoo.sub_unpaid_amount or 0) + add_amount
                zoo.save(update_fields=["sub_unpaid_amount"])
                total_amount += add_amount

                # --- ③ 契約終了日を1ヶ月延長 ---
                new_start = sub.end_day + timedelta(days=1)
                sub.end_day = _add_months(new_start, 1) - timedelta(days=1)

                # sign_mon（加入月数）も増やす
                sub.sign_mon = (sub.sign_mon or 0) + 1
                sub.save(update_fields=["end_day", "sign_mon"])

                updated += 1

                self.stdout.write(
                    f"{sub.member.username}: +{add_point}pt / "
                    f"+{add_amount}円 → 次回終了日 {sub.end_day}"
                )

        # ---- まとめ表示 ----
        self.stdout.write(self.style.SUCCESS("\n=== 月次更新完了 ==="))
        self.stdout.write(f"  対象契約      : {total} 件")
        self.stdout.write(f"  更新された契約: {updated} 件")
        self.stdout.write(f"  Zoo未設定でスキップ: {skipped_no_zoo} 件")
        self.stdout.write(f"  付与した合計スタポ: {total_points:,} pt")
        self.stdout.write(f"  Zoo に加算された合計額: {total_amount:,} 円")
        self.stdout.write(self.style.SUCCESS("===================================="))
