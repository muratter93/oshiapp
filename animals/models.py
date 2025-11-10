from django.db import models
from datetime import date
from django.utils import timezone

# -----------------------------------------

# animalsテーブル
class Animal(models.Model):
    animal_id = models.AutoField(primary_key=True)
    generic    = models.CharField("属", max_length=100, default="", blank=True, editable=False)
    specific   = models.CharField("種", max_length=100, default="", blank=True, editable=False)
    scientific = models.CharField("学名", max_length=200, default="", blank=True, editable=False)
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
    pic2 = models.ImageField("画像2", upload_to="animal_images/", blank=True, null=True, editable=False)
    pic3 = models.ImageField("画像3", upload_to="animal_images/", blank=True, null=True, editable=False)
    pic4 = models.ImageField("画像4", upload_to="animal_images/", blank=True, null=True, editable=False)
    pic5 = models.ImageField("画像5", upload_to="animal_images/", blank=True, null=True, editable=False)

    total_point = models.PositiveIntegerField("推しポイント", default=0)

# このモデルのテーブル名を明示指定
    class Meta:
        db_table = "animals"
        verbose_name = "Animal"
        verbose_name_plural = "Animals"

# オブジェクトの文字列表現
    def __str__(self):
        return f"{self.japanese}（{self.animal_id}） - {self.name}"

# 計算で得る年齢
    @property
    def age(self):
        """誕生日から自動計算した年齢を返す"""
        if self.birth is None:
            return None
        today = date.today()
        return today.year - self.birth.year - (
            (today.month, today.day) < (self.birth.month, self.birth.day)
        )

# -----------------------------------------

# zoosテーブル
class Zoo(models.Model):
    """動物園（animals アプリ内だがテーブルは 'zoos'）"""
    zoo_id = models.AutoField(primary_key=True)
    zoo_no = models.CharField("動物園No", max_length=32, unique=True, blank=True)
    zoo_name = models.CharField("動物園名", max_length=200)

    zoo_created_at = models.DateTimeField("登録日", default=timezone.now, editable=False)
    zoo_updated_at = models.DateTimeField("最終更新日", auto_now=True)

    class Meta:
        db_table = "zoos"
        verbose_name = "Zoo"
        verbose_name_plural = "Zoos"
        indexes = [models.Index(fields=["zoo_no"])]

    def __str__(self):
        return f"{self.zoo_no or '(未発番)'} / {self.zoo_name}"

    def save(self, *args, **kwargs):
        """初回保存時、zoo_no が空なら 'zoo{zoo_id}' を自動採番"""
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.zoo_no:
            self.zoo_no = f"zoo{self.zoo_id}"
            super().save(update_fields=["zoo_no"])

# -----------------------------------------

# pictureテーブル
class Picture(models.Model):
    """2枚目以降の画像（URL参照）。1枚目は Animal.pic1 を使用"""
    pic_id = models.AutoField(primary_key=True)

    # Animal は既存モデル名を参照
    animal = models.ForeignKey(
        "animals.Animal",
        on_delete=models.CASCADE,
        db_column="animal_fk",
        related_name="extra_pictures",
        verbose_name="動物",
    )

    image_url = models.TextField("画像URL")   # S3等のURL/キー
    caption = models.TextField("説明", blank=True)
    credit = models.CharField("クレジット", max_length=200, blank=True)

    # 2,3,4... を想定。1は Animal.pic1
    display_order = models.PositiveIntegerField("表示順", default=2)
    is_primary = models.BooleanField("サムネにする", default=False)

    pic_created_at = models.DateTimeField("登録日", default=timezone.now, editable=False)
    pic_updated_at = models.DateTimeField("最終更新日", auto_now=True)

    class Meta:
        db_table = "pictures"
        verbose_name = "追加画像（URL）"
        verbose_name_plural = "追加画像（URL）"
        constraints = [
            # 同じ動物内で並び順の重複を禁止
            models.UniqueConstraint(
                fields=["animal", "display_order"],
                name="uq_picture_order_per_animal",
            ),
        ]
        indexes = [
            models.Index(fields=["animal", "display_order"]),
            models.Index(fields=["animal", "is_primary"]),
        ]

    def __str__(self):
        return f"{self.animal_id}-pic{self.display_order}"