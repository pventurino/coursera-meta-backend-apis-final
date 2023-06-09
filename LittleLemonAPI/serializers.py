from rest_framework import serializers
from .models import MenuItem, Cart, Order, OrderItem
from django.contrib.auth.models import User

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta():
        model = MenuItem
        fields = ('id','title','price','category','featured')

class UserSerializer(serializers.ModelSerializer):
    class Meta():
        model = User
        fields = ('id','username','email')

class CartItemSerializer(serializers.ModelSerializer):
    class Meta():
        model = Cart
        fields = ('menuitem','quantity','unit_price','price')
        extra_kwargs = {
            'quantity': {'min_value': 0},
            'unit_price': {'read_only': True},
            'price': {'read_only': True},
        }

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta():
        model = OrderItem
        fields = ('__all__')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta():
        model = Order
        fields = ('__all__')
        extra_kwargs = {
            'user': {'read_only': True},
            'total': {'read_only': True},
            'date': {'read_only': True},
        }
