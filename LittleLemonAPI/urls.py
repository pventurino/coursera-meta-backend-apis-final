from django.urls import path
from .views import MenuItemsView, ManagersView

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
]