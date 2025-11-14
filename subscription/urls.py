from django.urls import path
from .views import purchase_done
from . import views

app_name = "subscription"

urlpatterns = [
    path("buy/<str:code>/done/", purchase_done, name="purchase_done"),
    path('plans/<int:animal_id>/', views.plan_list_by_animal, name='plan_list_by_animal'),
    path('confirm/<int:plan_id>/<int:animal_id>/', views.confirm_plan, name='confirm_plan'),
    path('join/<int:plan_id>/<int:animal_id>/', views.join_plan, name='join_plan'),

    path('cancel/<int:sub_member_id>/', views.cancel_subscription, name='cancel_subscription'), # 解約
    path('cancel/done/<int:sub_member_id>/', views.cancel_done, name='cancel_done'),

    path("reset_sub_members/", views.reset_sub_members, name="reset_sub_members"), # バルス
]
