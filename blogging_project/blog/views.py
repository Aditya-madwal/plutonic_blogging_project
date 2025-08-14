from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from .models import Blog, Like, Comment
from .serializers import BlogSerializer, BlogDetailSerializer, CommentSerializer
import os
from dotenv import load_dotenv
load_dotenv()

PAGE_SIZE_BLOGS = int(os.getenv('PAGE_SIZE_BLOGS'))
MAX_PAGE_SIZE_BLOGS = int(os.getenv('MAX_PAGE_SIZE_BLOGS'))
PAGE_SIZE_COMMENTS = int(os.getenv('PAGE_SIZE_COMMENTS'))
MAX_PAGE_SIZE_COMMENTS = int(os.getenv('MAX_PAGE_SIZE_COMMENTS'))
COMMENTS_ON_DETAIL_BLOG = int(os.getenv('COMMENTS_ON_DETAIL_BLOG'))

class BlogPagination(PageNumberPagination):
    page_size = PAGE_SIZE_BLOGS
    page_size_query_param = 'page_size'
    max_page_size = MAX_PAGE_SIZE_BLOGS

class CommentPagination(PageNumberPagination):
    page_size = PAGE_SIZE_COMMENTS
    page_size_query_param = 'page_size'
    max_page_size = MAX_PAGE_SIZE_COMMENTS


class BlogViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_blog(self, pk):
        return get_object_or_404(Blog, pk=pk)

    @swagger_auto_schema(
        operation_description="List all blogs with pagination",
        operation_summary="List Blogs"
    )
    @action(detail=False, methods=['get'])
    def list_blogs(self, request):
        queryset = Blog.objects.all().order_by('-created_at')
        paginator = BlogPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = BlogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Create a new blog",
        request_body=BlogSerializer,
        operation_summary="Create Blog"
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def create_blog(self, request):
        serializer = BlogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Retrieve a single blog",
        operation_summary="Get Blog"
    )
    @action(detail=True, methods=['get'])
    def get_blog_by_id(self, request, pk=None):
        blog = self.get_blog(pk)
        serializer = BlogSerializer(blog)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update a blog",
        request_body=BlogSerializer,
        operation_summary="Update Blog"
    )
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_blog(self, request, pk=None):
        blog = self.get_blog(pk)
        if blog.author != request.user:
            return Response({"error": "You can only modify your own blogs"}, status=status.HTTP_403_FORBIDDEN)
        serializer = BlogSerializer(blog, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a blog",
        operation_summary="Delete Blog"
    )
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def delete_blog(self, request, pk=None):
        blog = self.get_blog(pk)
        if blog.author != request.user:
            return Response({"error": "You can only delete your own blogs"}, status=status.HTTP_403_FORBIDDEN)
        blog.delete()
        return Response({"message": "Blog deleted successfully"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Like a blog",
        operation_summary="Like Blog"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like_blog(self, request, pk=None):
        blog = self.get_blog(pk)
        Like.objects.get_or_create(user=request.user, blog=blog)
        return Response({"message": "Blog liked"})

    @swagger_auto_schema(
        operation_description="Unlike a blog",
        operation_summary="Unlike Blog"
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unlike_blog(self, request, pk=None):
        blog = self.get_blog(pk)
        Like.objects.filter(user=request.user, blog=blog).delete()
        return Response({"message": "Blog unliked"})

    @swagger_auto_schema(
        operation_description="Add a comment to a blog",
        operation_summary="Add Comment",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['content'],
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def comment_blog(self, request, pk=None):
        blog = self.get_blog(pk)
        comment = Comment.objects.create(user=request.user, blog=blog, content=request.data.get("content"))
        return Response(CommentSerializer(comment).data)

    @swagger_auto_schema(
        operation_description="List all comments for a blog (paginated)",
        operation_summary="List Comments"
    )
    @action(detail=True, methods=['get'])
    def list_comments(self, request, pk=None):
        blog = self.get_blog(pk)
        queryset = blog.comments.all().order_by('-created_at')
        paginator = CommentPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CommentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_description="Get blog details with latest comments",
        operation_summary="Blog Details"
    )
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        blog = self.get_blog(pk)
        latest_comments = blog.comments.all().order_by('-created_at')[:COMMENTS_ON_DETAIL_BLOG]
        blog_data = BlogDetailSerializer(blog).data
        blog_data['latest_comments'] = CommentSerializer(latest_comments, many=True).data
        return Response(blog_data)
