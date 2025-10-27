from django.db.models.signals import post_save  # ユーザーが保存された後に動くシグナルを使う
from django.dispatch import receiver  # シグナルを受け取る関数を定義するためのデコレーター
from accounts.models import Member   # カスタムユーザーモデルに対応するための設定
from .models import Wallet  # ウォレットモデルをインポート


# 新規登録されたMemberに対してWalletを自動作成する
@receiver(post_save, sender=Member)

def create_wallet_for_new_user(sender, instance, created, **kwargs):
    # created が True の場合、新規登録されたユーザーであることを意味する
    if created:
        # 新しく登録されたユーザーに対して Wallet を作成する
        Wallet.objects.create(member=instance)
