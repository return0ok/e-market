from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from yaml import serialize
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.serializers import CreateUserSerializer
from apps.accounts.serializers import MyTokenObtainPairSerializer

# Create your views here.

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class RegisterAPIView(APIView):
    serializer_class = CreateUserSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': "success"}, status=201)
        return Response(serializer.errors, status=400)