from abc import abstractmethod
from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework.generics import ListCreateAPIView, DestroyAPIView, RetrieveUpdateAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import BasePermission, DjangoModelPermissionsOrAnonReadOnly
from rest_framework.exceptions import ParseError, NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from .models import MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, UserSerializer, CartItemSerializer, OrderSerializer
from datetime import date

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Manager').exists()

class IsDelivery(BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Delivery Crew').exists()

class ListPagination(PageNumberPagination):
    page_size = 10

# Create your views here.
class MenuItemsView(ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly,]
    pagination_class = ListPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        ordering = self.request.query_params.get('sort')

        if category:
            queryset = queryset.filter(category__slug=category)
        if search:
            queryset = queryset.filter(title__icontains=search)
        if ordering:
            ordering_fields = ordering.split(',')
            queryset = queryset.order_by(*ordering_fields)

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

class CartView(ListCreateAPIView, DestroyAPIView):
    serializer_class = CartItemSerializer
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user.id)
    
    def perform_create(self, serializer):
        """
        Adds the item to the cart
        If the item was already in the cart, updates the quantity and price
        If the quantity is 0, deletes removes the item from the cart
        """
        menuitem = serializer.validated_data.get('menuitem')

        # Delete any existing item for this user:menuitem (will be replaced)
        existing = Cart.objects.filter(user=self.request.user, menuitem=menuitem).first()
        if existing:
            existing.delete()

        # Only save if quantity is more than -0
        quantity = serializer.validated_data.get('quantity')
        if (quantity > 0):
            return serializer.save(
                user = self.request.user,
                unit_price = menuitem.price,
                price = menuitem.price * quantity,
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Deletes all cart items for the current user
        """
        Cart.objects.filter(user=self.request.user).delete()
        return Response(status=HTTP_204_NO_CONTENT)

class OrdersView(ListCreateAPIView):
    serializer_class = OrderSerializer
    pagination_class = ListPagination

    def get_queryset(self):
        groups = self.request.user.groups

        if groups.filter(name='Manager').exists():
            queryset = Order.objects.all()
        elif groups.filter(name='Delivery Crew').exists():
            queryset = Order.objects.filter(delivery_crew=self.request.user)
        else:
            queryset = Order.objects.filter(user=self.request.user)

        ordering = self.request.query_params.get('sort')
        if ordering:
            ordering_fields = ordering.split(',')
            queryset = queryset.order_by(*ordering_fields)
        
        return queryset

    def create(self, request, *args, **kwargs):
        cart = Cart.objects.filter(user=self.request.user)
        if len(cart) == 0:
            raise NotFound('cart is empty')

        # Calculate the total, to create the order
        total = 0
        for item in cart:
            total += item.price

        # Create the order
        order = Order.objects.create(
            user=self.request.user,
            total=total,
            date=date.today()
        )

        # Create the order items
        items = []
        for item in cart:
            items.append(OrderItem(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price
            ))
        OrderItem.objects.bulk_create(items)

        # Empty the cart
        cart.delete()

        serializer = OrderSerializer(Order.objects.get(id=order.id))
        return Response(serializer.data, HTTP_201_CREATED)

class SingleOrderView(RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        if self.request.user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif self.request.user.groups.filter(name='Delivery Crew').exists():
            return Order.objects.filter(delivery_crew=self.request.user)
        else:
            return Order.objects.filter(user=self.request.user)

    def get_permissions(self):
        if ['PUT','PATCH'].__contains__(self.request.method):
            return [(IsManager | IsDelivery)()]
        return super().get_permissions()

    def put(self, request, *args, **kwargs):
        # Should use only partial_update
        raise PermissionDenied()

    def perform_update(self, serializer):
        groups = self.request.user.groups
        allow=set()
        if groups.filter(name='Manager').exists():
            allow=set(['delivery_crew','status'])
        elif groups.filter(name='Delivery Crew').exists():
            allow=set(['status'])
        
        keys = set(serializer.validated_data.keys())
        forbidden = keys.difference(allow)

        if len(forbidden) > 0:
            data = {}
            for key in forbidden:
                data[key] = 'You do not have permission to modify this field'
            raise PermissionDenied(data)

        return super().perform_update(serializer)