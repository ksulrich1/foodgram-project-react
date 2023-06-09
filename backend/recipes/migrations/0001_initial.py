# Generated by Django 3.2.19 on 2023-05-18 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Ingredient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=200, verbose_name="Название ингредиента"
                    ),
                ),
                (
                    "measurement_unit",
                    models.CharField(
                        max_length=200, verbose_name="Еденицы измерения"
                    ),
                ),
            ],
            options={
                "verbose_name": "Ингредиент",
                "verbose_name_plural": "Ингредиенты",
                "ordering": ("name",),
            },
        ),
        migrations.AddConstraint(
            model_name="ingredient",
            constraint=models.UniqueConstraint(
                fields=("name", "measurement_unit"), name="unique_ingredient"
            ),
        ),
    ]
