from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, IngredientViewSet, TagViewSet, RecipeViewSet


router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("ingredients", IngredientViewSet, basename="ingredients")


urlpatterns = [
    path("", include(router.urls)),
    path("", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
]

router.register("tags", TagViewSet, basename="tags")
router.register("recipes", RecipeViewSet, basename="recipes")