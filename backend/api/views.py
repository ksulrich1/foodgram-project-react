from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.filters import IngredientSearch, RecipeFilter
from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    ShoppingList,
    Tag,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription, User

from .pagination import CustomPageNumberPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    IngredientSerailizer,
    RecipeCreateSerializer,
    RecipePageSerializer,
    RecipeReadSerializer,
    TagSerializer,
    UserFollowSerializer,
    UserSerializer,
)
from .utils import download_shopping_cart


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPageNumberPagination

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(following__user=user)
        page = self.paginate_queryset(queryset)
        serializer = UserFollowSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(User, id=id)

        if request.method == "POST":
            if user.id == author.id:
                return Response(
                    {"detail": "Нельзя подписаться на себя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Subscription.objects.filter(author=author, user=user).exists():
                return Response(
                    {"detail": "Вы уже подписаны!"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Subscription.objects.create(user=user, author=author)
            serializer = UserFollowSerializer(
                author, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            if not Subscription.objects.filter(
                user=user, author=author
            ).exists():
                return Response(
                    {"errors": "Вы не подписаны"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription = get_object_or_404(
                Subscription, user=user, author=author
            )
            subscription.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerailizer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = None
    filter_backends = (IngredientSearch,)
    search_fields = ("^name",)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = (
        "get",
        "post",
        "patch",
        "delete",
    )

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if self.request.method == "POST":
            if FavoriteRecipe.objects.filter(
                user=user, recipe=recipe
            ).exists():
                return Response(
                    {"errors": "Рецепт уже в избранном"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            FavoriteRecipe.objects.create(user=user, recipe=recipe)
            serializer = RecipePageSerializer(
                recipe, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not FavoriteRecipe.objects.filter(
            user=user, recipe=recipe
        ).exists():
            return Response(
                {"errors": "Рецепта нет в избранном"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite = get_object_or_404(FavoriteRecipe, user=user, recipe=recipe)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, pk=pk)

        if self.request.method == "POST":
            if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Уже в списке"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            ShoppingList.objects.create(user=user, recipe=recipe)
            serializer = RecipePageSerializer(
                recipe, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not ShoppingList.objects.filter(user=user, recipe=recipe).exists():
            return Response(
                {"errors": "Рецепта нет в списке покупок"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        shopping_cart = get_object_or_404(
            ShoppingList, user=user, recipe=recipe
        )
        shopping_cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        return download_shopping_cart(self, request)
