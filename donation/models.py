from django.db import models
from django.utils import timezone
from accounts.models import Member
from animals.models import Zoo  # 動物園モデルを利用

class Donation(models.Model):
    donation_id = models.AutoField(primary_key=True)

    # 寄付者（会員）
    donor = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        verbose_name="寄付者"
    )

    # 寄付対象（動物園）
    zoo = models.ForeignKey(
        Zoo,
        on_delete=models.CASCADE,
        verbose_name="寄付先の動物園"
    )

    # 寄付金額
    amount = models.PositiveIntegerField("寄付金額（円）")

    # 寄付者住所（証明書発行時に利用）
    address = models.CharField("寄付者住所", max_length=255, blank=True, null=True)

    # 任意の応援メッセージ
    message = models.TextField("応援メッセージ", blank=True, null=True)

    # 寄付日時
    created_at = models.DateTimeField("寄付日時", default=timezone.now)

    class Meta:
        db_table = "donations"
        verbose_name = "寄付"
        verbose_name_plural = "寄付"

    def __str__(self):
        return f"{self.donor.username} → {self.zoo.zoo_name}（{self.amount}円）"
