from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (FavoriteRecipe, Ingredient, IngredientInRecipe,
                            Recipe, ShoppingList, Tag)
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField
from users.models import Subscription, User


class UserSerializer(DjoserUserSerializer):
    """Сериализатор ползователя"""

    is_subscribed = serializers.BooleanField(default=False)

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ("is_subscribed",)


class UserFollowSerializer(serializers.ModelSerializer):
    """Сериализатор подписчика"""

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
        recipes = obj.recipes.all()
        serializer = RecipePageSerializer(
            recipes, many=True, context=self.context
        )
        return serializer.data

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
        if subscriber == author:
            raise ValidationError(
                detail="Попытка подписки на самого себя",
                code=status.HTTP_400_BAD_REQUEST,
            )
        return data


class IngredientSerailizer(serializers.ModelSerializer):
    """Сериализатор игредиента"""

    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега"""

    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор игредиента при создании рецепта"""

    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "amount", "name", "measurement_unit")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["id"] = instance.ingredient.id
        return data


class RecipePageSerializer(ModelSerializer):
    """Сериализатор для отображения рецептов на странице подписок."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class RecipeReadSerializer(ModelSerializer):
    """Сериализатор для получения рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source="recipeingredients", many=True
    )
    image = Base64ImageField()
    is_favorited = SerializerMethodField(read_only=True)
    is_in_shopping_cart = SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        return (
            not user.is_anonymous
            and FavoriteRecipe.objects.filter(user=user, recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        return (
            not user.is_anonymous
            and ShoppingList.objects.filter(user=user, recipe=obj).exists()
        )


class RecipeCreateSerializer(ModelSerializer):
    """Сериализатор для создания рецептов"""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def to_representation(self, instance):
        request = self.context.get("request")
        context = {"request": request}
        return RecipeReadSerializer(instance, context=context).data

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        for ingredient in ingredients:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient=ingredient.get("id"),
                amount=ingredient.get("amount"),
            )
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        if tags is not None:
            instance.tags.set(tags)
        ingredients = validated_data.pop("ingredients", None)
        if ingredients is not None:
            instance.ingredients.clear()
            for ingredient in ingredients:
                amount = ingredient["amount"]
                IngredientInRecipe.objects.update_or_create(
                    recipe=instance,
                    ingredient=ingredient.get("id"),
                    defaults={"amount": amount},
                )
        return super().update(instance, validated_data)
