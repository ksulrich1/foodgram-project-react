from django_filters import rest_framework
from rest_framework import FilterSet
from rest_framework.filters import SearchFilter
from django.contrib.auth import get_user_model

from recipes.models import Ingredient, Recipe


User = get_user_model()


class IngredientSearch(SearchFilter):
    search_param = 'name'

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(rest_framework.FilterSet):
    author = rest_framework.ModelChoiceFilter(queryset=User.objects.all())
    tags = rest_framework.AllValuesMultipleFilter(field_name="tags__slug")
    is_favorited = rest_framework.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = rest_framework.BooleanFilter(
        method="filter_is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user.pk
        if value and user:
            return queryset.filter(favorite__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user.pk
        if value and user:
            return queryset.filter(shopping__user=user)
        return queryset

    class Meta:
        model = Recipe
        fields = ("author", "tags", "is_favorited", "is_in_shopping_cart")
