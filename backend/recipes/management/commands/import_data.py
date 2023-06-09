import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        Ingredient.objects.all().delete()
        ingredient = os.path.join(settings.BASE_DIR, "data", "ingredients.csv")
        with open(ingredient) as file:
            reader = csv.reader(file)
            counter = 0
            for row in reader:
                print(row[0])
                Ingredient.objects.get_or_create(
                    name=row[0], measurement_unit=row[1]
                )
                counter += 1
        print(f"В базу данных успешно добавлены ингредиенты - {counter} шт. ✅")
