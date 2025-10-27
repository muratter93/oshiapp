from django.db import models

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