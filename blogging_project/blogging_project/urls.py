from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from blog.views import BlogViewSet
from user_auth.views import AuthViewSet
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Plutonic Blogging API",
        default_version='v1',
        description="A comprehensive blogging platform API with user authentication, blog management, and social features",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@plutonic-blog.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

router = DefaultRouter()
router.register(r'blogs', BlogViewSet, basename='blogs')
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    
    # Swagger Documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
