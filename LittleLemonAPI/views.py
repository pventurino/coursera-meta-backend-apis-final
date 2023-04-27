from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from .models import MenuItem
from .serializers import MenuItemSerializer

# Create your views here.
class MenuItemsView(ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

