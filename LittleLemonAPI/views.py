from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly
from .models import MenuItem
from .serializers import MenuItemSerializer

# Create your views here.
class MenuItemsView(ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly,]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        return queryset

