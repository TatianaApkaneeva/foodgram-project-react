import io

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db.models.aggregates import Sum
from django.db.models.expressions import Exists, OuterRef, Value
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen import canvas
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action, api_view
from rest_framework.permissions import (SAFE_METHODS, AllowAny,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAdminOrReadOnly
from recipes.models import (FavoriteRecipe, Ingredient, Recipe, ShoppingCart,
                            Subscribe, Tag)
from .serializers import (IngredientSerializer, RecipeReadSerializer,
                          RecipeWriteSerializer, SubscribeRecipeSerializer,
                          TagSerializer, SubscribeSerializer,
                          TokenSerializer, UserCreateSerializer,
                          UserListSerializer, UserPasswordSerializer,
                          SubscribeSerializer)


User = get_user_model()
FILENAME = 'shoppingcart.pdf'


class GetObjectMixin:
    """Миксина для удаления/добавления рецептов избранных/корзины."""

    serializer_class = SubscribeRecipeSerializer
    permission_classes = (AllowAny,)

    def get_object(self):
        recipe_id = self.kwargs['recipe_id']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        return recipe


class PermissionAndPaginationMixin:
    """Миксина для списка тегов и ингридиентов."""

    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class AddDeleteFavoriteRecipe(
        GetObjectMixin,
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):
    """Добавление и удаление рецепта в/из избранных."""

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        request.user.favorite_recipe.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.favorite_recipe.recipe.remove(instance)


class AddDeleteShoppingCart(
        GetObjectMixin,
        generics.RetrieveDestroyAPIView,
        generics.ListCreateAPIView):
    """Добавление и удаление рецепта в/из корзины."""

    def create(self, request, *args, **kwargs):
        instance = self.get_object()
        request.user.shopping_cart.recipe.add(instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        self.request.user.shopping_cart.recipe.remove(instance)


class AuthToken(ObtainAuthToken):
    """Авторизация пользователя."""

    serializer_class = TokenSerializer
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {'auth_token': token.key},
            status=status.HTTP_201_CREATED)


class UsersViewSet(UserViewSet):
    """Пользователи."""
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserListSerializer
        return UserCreateSerializer

    def perform_create(self, serializer):
        password = make_password(self.request.data['password'])
        serializer.save(password=password)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Получить на кого пользователь подписан."""

        user = request.user
        queryset = User.objects.filter(user=user)
        pages = self.paginate_queryset(queryset)
        serializer = UserListSerializer(
            pages, many=True,
            context={'request': request})
        return self.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['post', 'delete'],
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id=None):
        """Метод управления подписками."""

        if request.method == 'POST':
            user = request.user
            author = get_object_or_404(User, id=id)
            if user == author:
                return Response(
                    {'errors': 'Вы не можете подписаться сами на себя.'},
                    status=status.HTTP_400_BAD_REQUEST)
            if Subscribe.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на данного пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST)
            follower = Subscribe.objects.create(user=user, author=author)
            serializer = SubscribeSerializer(
                follower, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            user = request.user
            author = get_object_or_404(User, id=id)
            if user == author:
                return Response({
                    'errors': 'Вы не можете отписаться сами от себя.'
                })
            follower = Subscribe.objects.filter(user=user, author=author)
            if follower.exists():
                follower.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(serializer.data, {
                'errors': 'Подписка на данного пользователя отменена.'
            })
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipesViewSet(viewsets.ModelViewSet):
    """Рецепты."""

    queryset = Recipe.objects.all()
    filterset_class = RecipeFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def get_queryset(self):
        return Recipe.objects.annotate(
            is_favorited=Exists(
                FavoriteRecipe.objects.filter(
                    user=self.request.user, recipe=OuterRef('id'))),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    user=self.request.user,
                    recipe=OuterRef('id')))
        ).select_related('author').prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe'
        ) if self.request.user.is_authenticated else Recipe.objects.annotate(
            is_in_shopping_cart=Value(False),
            is_favorited=Value(False),
        ).select_related('author').prefetch_related(
            'tags', 'ingredients', 'recipe',
            'shopping_cart', 'favorite_recipe')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Качаем список с ингредиентами."""

        buffer = io.BytesIO()
        page = canvas.Canvas(buffer)
        arial = ttfonts.TTFont('Arial', 'data/arial.ttf')
        pdfmetrics.registerFont(arial)
        x_position, y_position = 50, 800
        shopping_cart = (
            request.user.shopping_cart.recipe.
            values(
                'ingredients__name',
                'ingredients__measurement_unit'
            ).annotate(amount=Sum('recipe__amount')).order_by())
        page.setFont('Arial', 14)
        if shopping_cart:
            indent = 20
            page.drawString(x_position, y_position, 'Cписок покупок:')
            for index, recipe in enumerate(shopping_cart, start=1):
                page.drawString(
                    x_position, y_position - indent,
                    f'{index}. {recipe["ingredients__name"]} - '
                    f'{recipe["amount"]} '
                    f'{recipe["ingredients__measurement_unit"]}.')
                y_position -= 15
                if y_position <= 50:
                    page.showPage()
                    y_position = 800
            page.save()
            buffer.seek(0)
            return FileResponse(
                buffer, as_attachment=True, filename=FILENAME)
        page.setFont('Arial', 24)
        page.drawString(
            x_position,
            y_position,
            'Cписок покупок пуст!')
        page.save()
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename=FILENAME)


class TagsViewSet(
        PermissionAndPaginationMixin,
        viewsets.ModelViewSet):
    """Список тэгов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientsViewSet(
        PermissionAndPaginationMixin,
        viewsets.ModelViewSet):
    """Список ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter


@api_view(['post'])
def set_password(request):
    """Изменить пароль."""

    serializer = UserPasswordSerializer(
        data=request.data,
        context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Пароль изменен!'},
            status=status.HTTP_201_CREATED)
    return Response(
        {'error': 'Введите верные данные!'},
        status=status.HTTP_400_BAD_REQUEST)
