from django.db import transaction
from drf_extra_fields.fields import Base64ImageField

from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from djoser.serializers import UserSerializer as DjoserUserSerializer

from users.models import User, Subscription
from recipes.models import Ingredient, Tag, IngredientInRecipe, Recipe


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.BooleanField(default=False)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ("is_subscribed",)


class UserFollowSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.BooleanField(default=True)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(default=0)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
        read_only_fields = ("email", "username", "first_name", "last_name")

    def get_recipes(self, obj):
        return []

    def validate(self, data):
        author = self.instance
        subscriber = self.context.get("request").user
        if Subscription.objects.filter(
            subscriber=subscriber, author=author
        ).exists():
            raise ValidationError(
                detail="Попытка повторной подписки",
                code=status.HTTP_400_BAD_REQUEST,
            )
        elif subscriber == author:
            raise ValidationError(
                detail="Попытка подписки на самого себя",
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data


class IngredientSerailizer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(
        source='ingredient.name'
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'amount',
        )


class ReciperSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = IngredientInRecipeSerializer(
        source="recipe_ingredientinrecipes", many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = UserSerializer(read_only=True)
    is_favorited = serializers.BooleanField(default=False, read_only=True)
    is_in_shopping_cart = serializers.BooleanField(
        default=False, read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            "image",
            "text",
            "cooking_time",
            "name",
            "ingredients",
            "tags",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def validate_tags(self, data):
        if not data or len(set(data)) < len(data):
            raise ValidationError("Отсутствует тэг")
        return data

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get("ingredients")
        if len({ingredient.get("id") for ingredient in ingredients}) < len(
            data
        ):
            raise ValidationError("Дубликат ингредиента")
        return data

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients_in_recipes = validated_data.pop(
            "recipe_ingredientinrecipes"
        )
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        IngredientInRecipe.objects.bulk_create(
            (
                IngredientInRecipe(
                    ingredient=ingredient_in_recipe["id"],
                    recipe=recipe,
                    amount=ingredient_in_recipe["amount"],
                )
                for ingredient_in_recipe in ingredients_in_recipes
            )
        )
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients_in_recipes = (
            validated_data.pop("recipe_ingredientinrecipes")
            if "recipe_ingredientinrecipes" in validated_data
            else {}
        )
        tags = validated_data.pop("tags") if "tags" in validated_data else {}
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.tags.set(tags)
        instance.ingredients.clear()
        IngredientInRecipe.objects.bulk_create(
            (
                IngredientInRecipe(
                    ingredient=ingredients_in_recipe["id"],
                    recipe=instance,
                    amount=ingredients_in_recipe["amount"],
                )
                for ingredients_in_recipe in ingredients_in_recipes
            )
        )
        return super().instance(instance, validated_data)

    def to_representation(self, instance):
        self.fields["tags"] = TagSerializer(many=True)
        return super().to_representation(instance)
