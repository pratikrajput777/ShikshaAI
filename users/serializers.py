from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
       class Meta:
           model = User
           fields = [
               "id",
               "username",
               "email",
               "first_name",
               "last_name",
               "target_role",
               "experience_years",
               "learning_style",
           ]


class UserCreateSerializer(serializers.ModelSerializer):
       class Meta:
           model = User
           fields = ["username", "email", "password", "target_role"]
           extra_kwargs = {"password": {"write_only": True}}

       def create(self, validated_data):
           password = validated_data.pop("password")
           user = User(**validated_data)
           user.set_password(password)
           user.save()
           return user


class UserListSerializer(serializers.ModelSerializer):
       class Meta:
           model = User
           fields = ["id", "username", "email", "target_role"]