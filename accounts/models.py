from django.contrib.auth.models import AbstractUser
from django.db import models
from animals.models import Zoo

class Member(AbstractUser):
    name        = models.CharField("名前", max_length=100, blank=True)
    birth       = models.DateField("生年月日", null=True, blank=True)
    postal_code = models.CharField("郵便番号", max_length=10, blank=True)
    address     = models.CharField("住所", max_length=255, blank=True)
    phone       = models.CharField("電話番号", max_length=20, blank=True)

    is_keeper   = models.BooleanField("飼育員", default=False)

    zoo = models.ForeignKey(
        Zoo,
        on_delete=models.SET_NULL,
        verbose_name="所属動物園",
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        verbose_name = "会員"
        verbose_name_plural = "会員"

    def __str__(self):
        return self.username
