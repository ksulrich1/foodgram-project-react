# Generated by Django 3.2.19 on 2023-05-25 19:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0005_auto_20230525_1900"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ingredientinrecipe",
            name="ingredient",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ingredientinrecipe",
                to="recipes.ingredient",
                verbose_name="Ингредиент",
            ),
        ),
        migrations.AlterField(
            model_name="ingredientinrecipe",
            name="recipe",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="ingredientinrecipe",
                to="recipes.recipe",
                verbose_name="Рецепт",
            ),
        ),
    ]
