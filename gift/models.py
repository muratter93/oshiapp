from django.db import models
from animals.models import Zoo

class Gift(models.Model):
    zoo = models.ForeignKey(
        Zoo,
        on_delete=models.CASCADE,
        related_name="gifts",
        verbose_name="動物園"
    )

    title = models.CharField("返礼品タイトル", max_length=200)
    description = models.TextField("返礼品説明", blank=True)

    main_image = models.ImageField(
        "メイン画像",
        upload_to="gift_images/main/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "gifts"
        verbose_name = "返礼品（メイン）"
        verbose_name_plural = "返礼品（メイン）"

    def __str__(self):
        return f"{self.title}（{self.zoo.zoo_name}）"


# サブ画像　説明
class GiftImage(models.Model):
    gift = models.ForeignKey(
        Gift,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="返礼品"
    )

    image = models.ImageField(
        "サブ画像",
        upload_to="gift_images/sub/"
    )

    caption = models.CharField(
        "キャプション（説明）",
        max_length=200,
        blank=True
    )

    display_order = models.PositiveIntegerField(
        "表示順", default=1
    )

    class Meta:
        db_table = "gift_images"
        ordering = ["display_order"]
        verbose_name = "返礼品追加画像"
        verbose_name_plural = "返礼品追加画像"

    def __str__(self):
        return f"{self.gift.title} - No.{self.display_order}"
