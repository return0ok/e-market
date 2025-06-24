from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainSerializer, AuthUser, TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token

from apps.accounts.models import User

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Добавляем пользовательские данные в полезную нагрузку
        if user.is_staff:
            token['group'] = 'admin'
        else:
            token['group'] = 'user'
            token['role'] = user.account_type
        return token

class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password')
    def validate_password(self, value: str) -> str:
        return make_password(value)
