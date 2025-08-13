from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from blog.views import BlogViewSet
from user_auth.views import AuthViewSet

router = DefaultRouter()
router.register(r'blogs', BlogViewSet, basename='blogs')
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
