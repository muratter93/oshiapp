from django.contrib.auth.models import AbstractUser
from django.db import models

class Member(AbstractUser):

    name        = models.CharField("名前", max_length=100, blank=True)
    postal_code = models.CharField("郵便番号", max_length=10, blank=True)
    address     = models.CharField("住所", max_length=255, blank=True)
    phone       = models.CharField("電話番号", max_length=20, blank=True)

    class Meta:
        verbose_name = "会員"
        verbose_name_plural = "会員"

    def __str__(self):
        return self.username

    """
    元から含まれているフィールド
    id          (PK)
    username    (一意)  ← ログインID
    email       
    password    (ハッシュ保存)
    """