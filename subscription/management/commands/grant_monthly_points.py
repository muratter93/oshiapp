from django.core.management.base import BaseCommand
from django.db import transaction
from datetime import date, timedelta
from subscription.models import SubMember, SubscribePlan
from money.models import Wallet
from subscription.models import _add_months

class Command(BaseCommand):
    help = '継続プランの会員に毎月スタポを付与し、終了日を次の月に延長します'

    def handle(self, *args, **options):
        today = date.today()
        subs_to_grant = SubMember.objects.filter(
            is_recurring=True,
            is_active=True,
            end_day=today
        )

        count = 0

        for sub in subs_to_grant:
            plan = sub.plan
            if plan.st_point > 0:
                with transaction.atomic():
                    wallet, _ = Wallet.objects.select_for_update().get_or_create(member=sub.member)
                    wallet.stanning_point_balance += plan.st_point
                    wallet.save(update_fields=["stanning_point_balance"])

                    # 終了日を次の月に延長
                    sub.end_day = _add_months(sub.end_day + timedelta(days=1), 1) - timedelta(days=1)
                    sub.save(update_fields=["end_day"])

                    count += 1
                    self.stdout.write(f"{sub.member.username} に {plan.st_point} pt を付与。新しい終了日: {sub.end_day}")

        self.stdout.write(f"{count} 件の継続プランにスタポを付与しました。")
