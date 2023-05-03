from django.urls import path
from .views import MenuItemsView, ManagersView, DeliveryCrewView, CartView, OrdersView, SingleOrderView

list = {
    'get':'list',
    'post':'create'
    }
detail = {
    'get':'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete':'destroy'
    }

urlpatterns = [
    path('menu-items', MenuItemsView.as_view(list)),
    path('menu-items/<int:pk>', MenuItemsView.as_view(detail)),
    path('groups/manager/users', ManagersView.as_view()),
    path('groups/manager/users/<int:pk>', ManagersView.as_view()),
    path('groups/delivery-crew/users', DeliveryCrewView.as_view()),
    path('groups/delivery-crew/users/<int:pk>', DeliveryCrewView.as_view()),
    path('cart/menu-items', CartView.as_view()),
    path('orders', OrdersView.as_view(), name='orders_list'),
    path('orders/<int:pk>', SingleOrderView.as_view(), name='orders_detail'),
]