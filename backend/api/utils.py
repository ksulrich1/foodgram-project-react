from django.db.models.aggregates import Sum
from django.http import HttpResponse
from recipes.models import IngredientInRecipe


def download_shopping_cart(self, request):
    ingredients = (
        IngredientInRecipe.objects.filter(
            recipe__shopping_list__user=request.user)
        .values("ingredient__name", "ingredient__measurement_unit")
        .annotate(amount=Sum("amount"))
    )
    text = ""
    for ingredient in ingredients:
        text += (
            f'•  {ingredient["ingredient__name"]}'
            f'({ingredient["ingredient__measurement_unit"]})'
            f'— {ingredient["amount"]}\n'
        )
    headers = {"Content-Disposition": "attchment; filename=shoping_cart.txt"}
    return HttpResponse(
        text, content_type="text/plain; charset=UTF-8", headers=headers
    )
