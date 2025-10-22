from django.db import models
from datetime import date

class Animal(models.Model):
    generic = models.CharField("属", max_length=100)
    specific = models.CharField("種", max_length=100)
    scientific = models.CharField("学名", max_length=200)
    japanese = models.CharField("和名", max_length=100)
    name = models.CharField("名前", max_length=100)
    SEX_CHOICES = [
        ("M", "オス"),
        ("F", "メス"),
        ("U", "不明"),
    ]
    sex = models.CharField("性別", max_length=1, choices=SEX_CHOICES, blank=True, null=True)
    birth = models.DateField("誕生日", blank=True, null=True)
    txt = models.TextField("説明文")
    pic1 = models.ImageField("画像1", upload_to="animal_images/")
    pic2 = models.ImageField("画像2", upload_to="animal_images/", blank=True, null=True)
    pic3 = models.ImageField("画像3", upload_to="animal_images/", blank=True, null=True)
    pic4 = models.ImageField("画像4", upload_to="animal_images/", blank=True, null=True)
    pic5 = models.ImageField("画像5", upload_to="animal_images/", blank=True, null=True)
    total_point = models.PositiveIntegerField("推しポイント", default=0)
    class Meta:
        db_table = "animals"
        verbose_name = "動物"
        verbose_name_plural = "動物"

    def __str__(self):
        return f"{self.japanese}（{self.scientific}） - {self.name}"
    @property

    def age(self):
        """誕生日から自動計算した年齢を返す"""

        if self.birth is None:

            return None

        today = date.today()

        return today.year - self.birth.year - (

            (today.month, today.day) < (self.birth.month, self.birth.day)

        )