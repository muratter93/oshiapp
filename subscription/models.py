from django.db import models

from django.conf import settings
from django.db import models
from datetime import date, timedelta

#サブスクプラン　マスターテーブル
class SubscribePlan(models.Model):
    code = models.CharField("プラン", max_length=10, unique=True)   # sb1..sb5 / by1..by3
    plan_name = models.CharField("プラン名", max_length=30)
    amount = models.PositiveIntegerField("金額")                    # 円
    st_point = models.PositiveIntegerField("スタポ", default=0)

    class Meta:
        db_table = "subscribe"
        verbose_name = "サブスクプラン"
        verbose_name_plural = "サブスクプラン"
        indexes = [models.Index(fields=["code"])]

    def __str__(self):
        return f"{self.code} ({self.plan_name})"


    #サブスク加入情報
def _add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    last_day = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m-1]
    day = min(d.day, last_day)
    return date(y, m, day)

class SubMember(models.Model):
    sub_member_id = models.AutoField(primary_key=True)  # ★主キー

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="会員",
        related_name="sub_memberships",
    )
    plan = models.ForeignKey(
        "subscription.SubscribePlan",
        on_delete=models.PROTECT,
        verbose_name="プラン",
        related_name="memberships",
    )

    sub = models.BooleanField("継続", default=True)   # sb* = True / by* = False
    sing_up = models.DateField("加入日", default=date.today)
    end_day = models.DateField("終了日", blank=True, null=True)
    sing_mon = models.PositiveIntegerField("合計加入月", default=0)


    class Meta:
        db_table = "sub_member"
        verbose_name = "サブスク会員"
        verbose_name_plural = "サブスク会員"
        indexes = [
            models.Index(fields=["member", "plan"]),
            models.Index(fields=["sing_up"]),
        ]

    def __str__(self):
        return f"{self.sub_member_id}: {self.member} - {self.plan.code}"

    def _auto_fill_by_plan(self):
        code = (self.plan.code or "").lower()
        if code.startswith("sb"):
            self.sub = True
            if not self.end_day:
                self.end_day = _add_months(self.sing_up, 1) - timedelta(days=1)
        elif code in ("by1", "by2", "by3"):
            self.sub = False
            months = {"by1": 3, "by2": 6, "by3": 12}[code]
            if not self.end_day:
                self.end_day = _add_months(self.sing_up, months) - timedelta(days=1)

    def _calc_total_months(self):
        if self.end_day and self.sing_up:
            self.sing_mon = max(
                0,
                (self.end_day.year - self.sing_up.year) * 12 + (self.end_day.month - self.sing_up.month)
            )

    def save(self, *args, **kwargs):
        self._auto_fill_by_plan()
        self._calc_total_months()
        super().save(*args, **kwargs)