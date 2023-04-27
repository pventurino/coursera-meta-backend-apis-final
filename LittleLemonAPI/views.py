from abc import abstractmethod
from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework.generics import ListCreateAPIView, DestroyAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import BasePermission, DjangoModelPermissionsOrAnonReadOnly
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from .models import MenuItem
from .serializers import MenuItemSerializer, UserSerializer

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists()

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

class GroupsView(ListCreateAPIView, DestroyAPIView):
    @abstractmethod
    def __getgroupname__(self):
        pass
    
    serializer_class = UserSerializer
    permission_classes = [IsManager,]

    def get_queryset(self):
        return User.objects.filter(groups__name=self.__getgroupname__())

    def create(self, request, *args, **kwargs):
        username = request.POST.get('username')
        if username == None:
            raise ParseError({'username':'Missing required parameter'})
        try:
            usr = User.objects.get(username=username)
            grp = Group.objects.get(name=self.__getgroupname__())
            usr.groups.add(grp)
            return Response(status=HTTP_201_CREATED)
        except:
            raise NotFound()
        
    def destroy(self, request, *args, **kwargs):
        try:
            usr = self.get_object()
            grp = Group.objects.get(name=self.__getgroupname__())
            usr.groups.remove(grp)
            return Response(status=HTTP_204_NO_CONTENT)
        except:
            raise NotFound()
        
class ManagersView(GroupsView):
    def __getgroupname__(self):
        return 'Manager'

class DeliveryCrewView(GroupsView):
    def __getgroupname__(self):
        return 'Delivery crew'
