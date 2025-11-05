from django.conf import settings
from django.db import models

class Wallet(models.Model):
    member = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name='会員'
    )
    cheer_coin_balance = models.PositiveIntegerField(default=0)
    stanning_point_balance = models.PositiveIntegerField(default=0)

    def add_cheer_coins(self, yen_amount):
        if yen_amount >= 5000:
            coins = 7000
        elif yen_amount >= 3000:
            coins = 3600    
        elif yen_amount >= 1000:
            coins = 1000
        elif yen_amount >= 100:
            coins = 100    
        else:
            coins = yen_amount
        self.cheer_coin_balance += coins
        self.stanning_point_balance += coins // 100
        self.save()

    def __str__(self):
        return f"{self.member.username} のウォレット"


# --- チアコ購入履歴 ---
class CheerCoinPurchase(models.Model):
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cheercoin_purchases',
        verbose_name='購入者'
    )
    coins = models.PositiveIntegerField(verbose_name='購入チアコイン数')
    price = models.PositiveIntegerField(verbose_name='購入金額（円）')
    purchased_at = models.DateTimeField(auto_now_add=True, verbose_name='購入日時')

    def __str__(self):
        return f"{self.member.username} が {self.coins} チアコイン購入 ({self.price}円)"