from django.contrib import admin
from .models import Animal

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
  list_display = (
    "animal_id", "japanese", "scientific", "name", "sex", "birth", "age", "total_point"
  )
  list_display_links = ("animal_id", "japanese", "name")
  list_filter = ("sex", "generic", "specific")
  search_fields = ("japanese", "scientific", "name", "generic", "specific")
  list_per_page = 20