from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from django.db.models import BooleanField, Case, When
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response

from recipes.filters import IngredientSearch, RecipeFilter
from core.pagination import CustomPageNumberPagination

from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    UserFollowSerializer,
    IngredientSerailizer,
    TagSerializer,
    RecipeReadSerializer,
    RecipeCreateSerializer,
    RecipePageSerializer,
)
from .utils import download_shopping_cart

from users.models import User, Subscription

from recipes.models import (
    Ingredient,
    Tag,
    FavoriteRecipe,
    IngredientInRecipe,
    Recipe,
    ShoppingList,
)


class UserViewSet(DjoserUserViewSet):
    def get_queryset(self):
        request_user = self.request.user
        queryset = super().get_queryset()
        if request_user.is_authenticated:
            queryset = (
                super()
                .get_queryset()
                .annotate(
                    is_subscribed=Case(
                        When(
                            author_subscriptions__subscriber=request_user,
                            then=True,
                        ),
                        default=False,
                        output_field=BooleanField(),
                    )
                )
            )
        return queryset

    @action(methods=["GET"], detail=False)
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    @action(
        methods=["GET"], detail=False, permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request, *args, **kwargs):
        authors_id = request.user.subscriber_subscriptions.values_list(
            "author_id", flat=True
        )
        queryset = User.objects.filter(id__in=authors_id)
        page = self.paginate_queryset(queryset)
        serializer = UserFollowSerializer(
            page, many=True, context=self.get_serializer_context()
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["POST"], detail=True, permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        subscriber = request.user
        author = get_object_or_404(User, pk=kwargs.get("id"))
        serializer = UserFollowSerializer(
            author, data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        Subscription.objects.create(subscriber=subscriber, author=author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, *args, **kwargs):
        author = get_object_or_404(User, pk=kwargs.get("id"))
        get_object_or_404(Subscription, subscriber=request.user, author=author)
        author.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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

        if self.request.method == "DELETE":
            if not FavoriteRecipe.objects.filter(
                user=user, recipe=recipe
            ).exists():
                return Response(
                    {"errors": "Рецепта нет в избранном"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite = get_object_or_404(
                FavoriteRecipe, user=user, recipe=recipe
            )
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

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

        if self.request.method == "DELETE":
            if not ShoppingList.objects.filter(
                user=user, recipe=recipe
            ).exists():
                return Response(
                    {"errors": "Рецепта нет в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            shopping_cart = get_object_or_404(
                ShoppingList, user=user, recipe=recipe
            )
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(
        detail=False, methods=["get"], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        return download_shopping_cart(self, request)
