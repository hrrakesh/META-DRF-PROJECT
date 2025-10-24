from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MenuItemViewSet, ManagerGroupView, DeliveryCrewGroupView, CartView, OrderViewSet


router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('menu-items', MenuItemViewSet, basename='menuitem')
router.register('orders', OrderViewSet, basename='order')


urlpatterns = [
    path('', include(router.urls)),
    path('groups/manager/users', ManagerGroupView.as_view()),
    path('groups/manager/users/<int:user_id>', ManagerGroupView.as_view()),
    path('groups/delivery-crew/users', DeliveryCrewGroupView.as_view()),
    path('groups/delivery-crew/users/<int:user_id>', DeliveryCrewGroupView.as_view()),
    path('cart/menu-items', CartView.as_view()),
]