from django import forms
from .models import Goods

class GoodsForm(forms.ModelForm):
    class Meta:
        model = Goods
        fields = ['name', 'description', 'image', 'required_stanning_points', 'stock']
        labels = {
            'name': 'グッズ名',
            'description': '説明',
            'image': '画像',
            'required_stanning_points': '必要スターポイント',
            'stock': '在庫数',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
