from django.db import IntegrityError
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from django.db.models import BooleanField, Case, When
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.filters import IngredientSearch, RecipeFilter
from core.pagination import CustomPageNumberPagination

from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (UserFollowSerializer,
                          IngredientSerailizer,
                          TagSerializer,
                          RecipeMinifiedSerializer,
                          RecipeWriteSerializer,
                          RecipeReadSerializer)

from users.models import User, Subscription

from recipes.models import (
    Ingredient,
    Tag,
    FavoriteRecipe,
    IngredientInRecipe,
    Recipe,
    ShoppingList
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
        get_object_or_404(Subscription, subscriber=request.user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerailizer
    pagination_class = None
    filter_backends = (IngredientSearch)
    search_fields = ("^name",)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = CustomPageNumberPagination
    permission_classes = (IsAuthorOrAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete',)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @staticmethod
    def add_to_list(model, user, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        try:
            model.objects.create(user=user, recipe=recipe)
        except IntegrityError:
            return Response(
                {'errors': 'Дублирование добавления.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = RecipeMinifiedSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_from_list(model, user, pk):
        instance = model.objects.filter(user=user, recipe__id=pk)
        if not instance.exists():
            return Response(
                {'errors': 'Рецепт отсутствует в списке.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        if request.method == 'POST':
            return self.add_to_list(FavoriteRecipe, request.user, pk)
        return self.delete_from_list(FavoriteRecipe, request.user, pk)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        if request.method == 'POST':
            return self.add_to_list(ShoppingList, request.user, pk)
        return self.delete_from_list(ShoppingList, request.user, pk)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        ingredients = (
            IngredientInRecipe.objects
            .filter(recipe__shopping__user=request.user)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
        )
        shopping_cart = [f'Список покупок {request.user}.\n']
        for ingredient in ingredients:
            shopping_cart.append(
                f'{ingredient["ingredient__name"]} - '
                f'{ingredient["amount"]} '
                f'{ingredient["ingredient__measurement_unit"]}\n'
            )
        file = f'{request.user}_shopping_cart.txt'
        response = HttpResponse(shopping_cart, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename={file}'
        return response
