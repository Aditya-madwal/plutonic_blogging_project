from rest_framework import viewsets, permissions, status
from django.contrib.auth import authenticate
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import RegisterSerializer, UserSerializer

class AuthViewSet(viewsets.ViewSet):
    """
    Authentication ViewSet for user registration, login, and profile management.
    
    Provides endpoints for user registration, authentication, and profile retrieval.
    """
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Register a new user account",
        operation_summary="User Registration",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                "User created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT, description="User data"),
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description="Authentication token")
                    }
                )
            ),
            400: "Bad Request - Invalid registration data"
        }
    )
    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Register a new user account and return user data with authentication token.
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"user": UserSerializer(user).data, "token": token.key}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Authenticate user and return authentication token",
        operation_summary="User Login",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Username"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="Password")
            }
        ),
        responses={
            200: openapi.Response(
                "Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT, description="User data"),
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description="Authentication token")
                    }
                )
            ),
            401: "Unauthorized - Invalid credentials"
        }
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Authenticate user with username and password, return user data and authentication token.
        """
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"user": UserSerializer(user).data, "token": token.key})

    @swagger_auto_schema(
        operation_description="Get current authenticated user's profile information",
        operation_summary="Get User Profile",
        responses={
            200: openapi.Response("User profile", schema=openapi.Schema(type=openapi.TYPE_OBJECT, description="User profile data")),
            401: "Unauthorized - Authentication required"
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Retrieve the current authenticated user's profile information.
        """
        return Response(UserSerializer(request.user).data)
