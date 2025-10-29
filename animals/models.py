from django.db import models
from datetime import date
from django.db import models, transaction
from django.db.models import F


#動物テーブル
class Animal(models.Model):
    animal_id = models.CharField("動物ID", max_length=15, primary_key=True)
    generic = models.CharField("属", max_length=100)
    specific = models.CharField("種", max_length=100)
    scientific = models.CharField("学名", max_length=200)
    japanese = models.CharField("和名", max_length=100)
    zoo = models.ForeignKey("Zoo", on_delete=models.PROTECT, verbose_name="所属動物園", null=True, blank=True)
    name = models.CharField("名前", max_length=100)

    SEX_CHOICES = [
        ("M", "オス"),
        ("F", "メス"),
        ("U", "不明"),
    ]

    sex = models.CharField("性別", max_length=1, choices=SEX_CHOICES, blank=True, null=True)
    birth = models.DateField("誕生日", blank=True, null=True)
    txt = models.TextField("説明文", blank=True)

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

    def save(self, *args, **kwargs):
        if not self.animal_id:
            if not self.zoo_id:
                raise ValueError("zoo を先にセットしてください（animal_id の自動採番に必要）")
            with transaction.atomic():
                seq, _ = ZooSequence.objects.select_for_update().get_or_create(zoo=self.zoo)
                local_no = seq.next_no
                seq.next_no = F("next_no") + 1
                seq.save()
            self.animal_id = f"{self.zoo_id}_{local_no:04d}"
        super().save(*args, **kwargs)

    @property
    def age(self):
        """誕生日から自動計算した年齢を返す"""
        if self.birth is None:
            return None
        today = date.today()
        return today.year - self.birth.year - (
            (today.month, today.day) < (self.birth.month, self.birth.day)
        )


# 連番を管理するテーブル（各動物園ごとに採番）
class ZooSequence(models.Model):
    zoo = models.OneToOneField("Zoo", on_delete=models.CASCADE, primary_key=True, related_name="seq")
    next_no = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "zoo_sequence"


#動物園テーブル
class Zoo(models.Model):
    zoo_id = models.CharField("動物園ID", max_length=10, primary_key=True)
    zoo_name = models.CharField("動物園名", max_length=100)

    class Meta:
        db_table = "zoo"
        verbose_name = "動物園"
        verbose_name_plural = "動物園"

    def __str__(self):
        return self.zoo_name