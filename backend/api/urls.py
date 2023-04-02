from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (AuthToken, IngredientsViewSet,
                       RecipesViewSet, TagsViewSet, UsersViewSet, set_password)

app_name = 'api'

router = DefaultRouter()
router.register('users', UsersViewSet)
router.register('tags', TagsViewSet)
router.register('ingredients', IngredientsViewSet)
router.register('recipes', RecipesViewSet)


urlpatterns = [
     path(
          'auth/token/login/',
          AuthToken.as_view(),
          name='login'),
     path(
          'users/set_password/',
          set_password,
          name='set_password'),
     path('', include(router.urls)),
     path('', include('djoser.urls')),
     path('auth/', include('djoser.urls.authtoken')),
]
