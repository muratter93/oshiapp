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
