from rest_framework import serializers
from .models import MenuItem
from django.contrib.auth.models import User

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta():
        model = MenuItem
        fields = ('id','title','price','category','featured')

class UserSerializer(serializers.ModelSerializer):
    class Meta():
        model = User
        fields = ('id','username','email')