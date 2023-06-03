from django.contrib import admin
from django.contrib.admin import display

from .models import (FavoriteRecipe, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingList, Tag)


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "measurement_unit",
    )
    list_filter = ("name",)
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "color",
        "slug",
    )


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "text",
        "author",
        "pub_date",
        "image",
        "cooking_time",
        "added_to_favorite",
    )
    inlines = (IngredientInRecipeInline,)
    list_filter = (
        "name",
        "author",
        "tags",
    )
    search_fields = (
        "name",
        "author__username",
        "tags__name",
    )

    @display(description="Общее число в избранном")
    def added_to_favorite(self, obj):
        return obj.favorite.count()


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = (
        "recipe",
        "ingredient",
        "amount",
    )


@admin.register(FavoriteRecipe)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "recipe",
    )


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "recipe",
    )
