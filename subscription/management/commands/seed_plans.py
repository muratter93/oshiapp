# coding: utf-8
from django.core.management.base import BaseCommand
from subscription.models import SubscribePlan

PLANS = [
    {"code":"sb1","plan_name":"1,000円/月","amount":1000,"st_point":15},
    {"code":"sb2","plan_name":"3,000円/月","amount":3000,"st_point":50},
    {"code":"sb3","plan_name":"5,000円/月","amount":5000,"st_point":90},
    {"code":"sb4","plan_name":"8,000円/月","amount":8000,"st_point":150},
    {"code":"sb5","plan_name":"10,000円/月","amount":10000,"st_point":200},
    {"code":"by1","plan_name":"3ヶ月","amount":3000,"st_point":40},
    {"code":"by2","plan_name":"6ヶ月","amount":5000,"st_point":80},
    {"code":"by3","plan_name":"12ヶ月","amount":10000,"st_point":180},
]

class Command(BaseCommand):
    help = "SubscribePlan をシード（update_or_create で安全に反映）"

    def handle(self, *args, **kwargs):
        for row in PLANS:
            SubscribePlan.objects.update_or_create(code=row["code"], defaults=row)
        self.stdout.write(self.style.SUCCESS("Seeded SubscribePlan"))