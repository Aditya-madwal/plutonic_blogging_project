from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from user_auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import RegisterSerializer, UserSerializer

class IsSuperUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Create a superuser and return JWT tokens",
        operation_summary="Create Superuser",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password', 'email'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING)
            }
        ),
        responses={
            201: openapi.Response(
                "Superuser created",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    @action(detail=False, methods=['post'])
    def create_superuser(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")
        if not username or not password or not email:
            return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_superuser(username=username, password=password, email=email)
        user.is_active = True
        user.save()
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        return Response({
            "user": UserSerializer(user).data,
            "access": str(access_token),
            "refresh": str(refresh)
        }, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Register a new user account (superuser only)",
        operation_summary="User Registration (Superuser only)",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                "User created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            400: "Bad Request"
        }
    )
    @action(detail=False, methods=['post'], permission_classes=[IsSuperUser])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Set created_by to the superuser who created this user
        user.created_by = request.user
        user.save()
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
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
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

    @swagger_auto_schema(
        operation_description="Refresh access token using a valid refresh token",
        operation_summary="Refresh Access Token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token")
            }
        ),
        responses={
            200: openapi.Response(
                "Token refreshed",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description="New access token")
                    }
                )
            ),
            400: "Bad Request - Invalid refresh token"
        }
    )
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token
            return Response({"access": str(access_token)}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid refresh token"}, status=status.HTTP_400_BAD_REQUEST)
