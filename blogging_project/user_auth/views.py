from rest_framework import viewsets, permissions, status
from django.contrib.auth import authenticate
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
# from django.contrib.auth.models import User
from user_auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import RegisterSerializer, UserSerializer

class AuthViewSet(viewsets.ViewSet):
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
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description="Access token"),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token")
                    }
                )
            ),
            400: "Bad Request - Invalid registration data"
        }
    )
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return Response({
            "user": UserSerializer(user).data, 
            "access": str(access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Authenticate user and return JWT tokens",
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
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description="Access token"),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token")
                    }
                )
            ),
            401: "Unauthorized - Invalid credentials"
        }
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        return Response({
            "user": UserSerializer(user).data, 
            "access": str(access_token),
            "refresh": str(refresh)
        })

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
        return Response(UserSerializer(request.user).data)
