from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator


User = get_user_model()

MAX_LEN = 200
HEX_LEN = 7
DEFAULT_HEX = "2c3cba"


class Ingredient(models.Model):
    name = models.CharField("Название ингредиента", max_length=MAX_LEN)
    measurement_unit = models.CharField(
        "Единицы измерения", max_length=MAX_LEN
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredient"
            )
        ]

    def __str__(self):
        return f"{self.name}, {self.measurement_unit}"


class Tag(models.Model):
    name = models.CharField("Название тэга", max_length=MAX_LEN)
    slug = models.SlugField("Адрес тэга", unique=True, max_length=MAX_LEN)
    color = models.CharField(
        "Цвет(HEX)", max_length=HEX_LEN, default=DEFAULT_HEX
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return f"{self.name}"


class Recipe(models.Model):
    name = models.CharField("Название рецепта", max_length=MAX_LEN)
    image = models.ImageField("Изображение", upload_to="recipes/images/")
    text = models.TextField("Описание")
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="recipes",
        verbose_name="Автор",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name="Ингредиенты",
        related_name="recipes",
        through="IngredientInRecipe",
    )
    tags = models.ManyToManyField(
        Tag, verbose_name="Теги", related_name="recipes"
    )
    cooking_time = models.PositiveIntegerField(
        "Время приготовления",
        validators=(
            MinValueValidator(
                1, message="Время приготовления должно быть больше 1 минуты"
            ),
        ),
    )
    pub_date = models.DateTimeField(
        verbose_name="Дата публикации", auto_now_add=True
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return f"{self.name} ({self.author})"


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="recipeingredients",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipeingredients",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество ингредиента",
        validators=(
            MinValueValidator(1, message="Добавьте больше игредиентов"),
        ),
    )

    class Meta:
        verbose_name = "Количество ингредиента"
        verbose_name_plural = "Количество ингредиентов"
        constraints = (
            models.UniqueConstraint(
                fields=("ingredient", "recipe"),
                name="ingredient_in_recipe_repetition",
            ),
        )


class ShoppingList(models.Model):
    """Модель для списка покупок."""

    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="shopping_list",
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Рецепт в корзине",
        on_delete=models.CASCADE,
        related_name="shopping_list",
    )

    class Meta:
        verbose_name = "Список покупок"
        verbose_name_plural = "Списки покупок"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_shoppings_recipe",
            )
        ]

    def __str__(self):
        return f"{self.user} added {self.recipe}"


class FavoriteRecipe(models.Model):
    """Модель для понравившихся рецептов."""

    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.CASCADE,
        related_name="favorite",
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name="Понравившийся рецепт",
        on_delete=models.CASCADE,
        related_name="favorite",
    )

    class Meta:
        verbose_name = "Избранный рецепт"
        verbose_name_plural = "Избранные рецепты"
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"),
                name="unique_favorite_recipe",
            )
        ]

    def __str__(self):
        return f"{self.user} added {self.recipe}"
