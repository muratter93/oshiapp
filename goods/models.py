from django.db import models

from django.conf import settings
from django.db import models

# --- グッズモデル ---
class Goods(models.Model):
    name = models.CharField(max_length=100, verbose_name='グッズ名')
    description = models.TextField(verbose_name='説明')
    image = models.ImageField(upload_to='goods_images/', verbose_name='画像')
    required_stanning_points = models.PositiveIntegerField(verbose_name='必要スターポイント')
    stock = models.PositiveIntegerField(default=0, verbose_name='在庫数')

    def __str__(self):
        return self.name
    
# 詳細ページ用の画像モデル
class GoodsImage(models.Model):
    goods = models.ForeignKey(Goods, on_delete=models.CASCADE, related_name='detail_images')
    image = models.ImageField(upload_to='goods_detail_images/', verbose_name='詳細画像')
    order = models.PositiveIntegerField(default=0, verbose_name='並び順')  # 表示順を管理したいとき

    def __str__(self):
        return f"{self.goods.name} - {self.id}"    
    



# --- 注文モデル ---
class Order(models.Model):
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_stanning_points = models.PositiveIntegerField()
    shipping_address = models.TextField()
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.member.username} の注文"

# --- 注文アイテムモデル ---
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    goods = models.ForeignKey(Goods, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_required_stanning_points(self):
        return self.goods.required_stanning_points * self.quantity

    def __str__(self):
        return f"{self.goods.name} x {self.quantity}"
    

#--- 買い物かごモデル ---
class CartItem(models.Model):
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    goods = models.ForeignKey(Goods, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def get_required_stanning_points(self):
        return self.goods.required_stanning_points * self.quantity

    def __str__(self):
        return f"{self.goods.name} x {self.quantity}（{self.member.username}）"    
