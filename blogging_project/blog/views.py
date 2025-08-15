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
        operation_summary="List Blogs",
        operation_description="Retrieve a paginated list of all blogs.",
        responses={200: BlogSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def list_blogs(self, request):
        queryset = Blog.objects.all().order_by('-created_at')
        paginator = BlogPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = BlogSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Create Blog",
        operation_description="Create a new blog post. **Requires authentication**.",
        request_body=BlogSerializer,
        responses={201: BlogSerializer}
    )
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def create_blog(self, request):
        serializer = BlogSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            blog = serializer.save()
            return Response(BlogSerializer(blog, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Get Blog by ID",
        operation_description="Retrieve a blog by its ID.",
        responses={200: BlogSerializer, 404: "Not Found"}
    )
    @action(detail=True, methods=['get'])
    def get_blog_by_id(self, request, pk=None):
        blog = self.get_blog(pk)
        serializer = BlogSerializer(blog)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Update Blog",
        operation_description="Update a blog (partial update). **Only the author can update.**",
        request_body=BlogSerializer,
        responses={200: BlogSerializer, 403: "Forbidden", 404: "Not Found"}
    )
    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def update_blog(self, request, pk=None):
        blog = self.get_blog(pk)
        if blog.author != request.user:
            return Response({"error": "You can only modify your own blogs"}, status=status.HTTP_403_FORBIDDEN)
        serializer = BlogSerializer(blog, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            blog = serializer.save()
            return Response(BlogSerializer(blog, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Delete Blog",
        operation_description="Delete a blog post. **Only the author can delete.**",
        responses={200: "Blog deleted", 403: "Forbidden", 404: "Not Found"}
    )
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def delete_blog(self, request, pk=None):
        blog = self.get_blog(pk)
        if blog.author != request.user:
            return Response({"error": "You can only delete your own blogs"}, status=status.HTTP_403_FORBIDDEN)
        blog.delete()
        return Response({"message": "Blog deleted successfully"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Like Blog",
        operation_description="Like a blog post. Creates a like if it doesn't already exist.",
        responses={200: openapi.Response("Success", openapi.Schema(type=openapi.TYPE_OBJECT, properties={
            "message": openapi.Schema(type=openapi.TYPE_STRING)
        }))}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like_blog(self, request, pk=None):
        blog = self.get_blog(pk)
        Like.objects.get_or_create(user=request.user, blog=blog)
        return Response({"message": "Blog liked"})

    @swagger_auto_schema(
        operation_summary="Unlike Blog",
        operation_description="Remove a like from a blog post.",
        responses={200: openapi.Response("Success", openapi.Schema(type=openapi.TYPE_OBJECT, properties={
            "message": openapi.Schema(type=openapi.TYPE_STRING)
        }))}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def unlike_blog(self, request, pk=None):
        blog = self.get_blog(pk)
        Like.objects.filter(user=request.user, blog=blog).delete()
        return Response({"message": "Blog unliked"})

    @swagger_auto_schema(
        operation_summary="Add Comment",
        operation_description="Add a comment to a blog post. **Requires authentication**.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['content'],
            properties={'content': openapi.Schema(type=openapi.TYPE_STRING)}
        ),
        responses={201: CommentSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def comment_blog(self, request, pk=None):
        blog = self.get_blog(pk)
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            comment = serializer.save()
            comment.blog = blog
            comment.save()
            return Response(CommentSerializer(comment, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="List Comments",
        operation_description="Retrieve all comments for a blog (paginated).",
        responses={200: CommentSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def list_comments(self, request, pk=None):
        blog = self.get_blog(pk)
        queryset = blog.comments.all().order_by('-created_at')
        paginator = CommentPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CommentSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Blog Details",
        operation_description="Retrieve blog details with the latest comments.",
        responses={200: BlogDetailSerializer}
    )
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        blog = self.get_blog(pk)
        latest_comments = blog.comments.all().order_by('-created_at')[:COMMENTS_ON_DETAIL_BLOG]
        blog_data = BlogDetailSerializer(blog, context={'request': request}).data
        blog_data['latest_comments'] = CommentSerializer(latest_comments, many=True, context={'request': request}).data
        return Response(blog_data)

    @swagger_auto_schema(
        operation_summary="Update Comment",
        operation_description="Update a comment. Only the comment's author can update.",
        request_body=CommentSerializer,
        responses={200: CommentSerializer, 403: "Forbidden", 404: "Not Found"}
    )
    @action(detail=True, methods=['patch'], url_path='update_comment/(?P<comment_id>[^/.]+)', permission_classes=[permissions.IsAuthenticated])
    def update_comment(self, request, pk=None, comment_id=None):
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.user != request.user:
            return Response({"error": "You can only update your own comments"}, status=status.HTTP_403_FORBIDDEN)
        serializer = CommentSerializer(comment, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            comment = serializer.save()
            return Response(CommentSerializer(comment, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
