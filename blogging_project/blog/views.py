from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Blog, Like, Comment
from .serializers import BlogSerializer, BlogDetailSerializer, CommentSerializer
from .constants import *

class BlogPagination(PageNumberPagination):
    page_size = PAGE_SIZE_BLOGS
    page_size_query_param = 'page_size'
    max_page_size = MAX_PAGE_SIZE_BLOGS

class CommentPagination(PageNumberPagination):
    page_size = PAGE_SIZE_COMMENTS
    page_size_query_param = 'page_size'
    max_page_size = MAX_PAGE_SIZE_COMMENTS

class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all().order_by('created_at')
    serializer_class = BlogSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = BlogPagination
    
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Retrieve a list of all blog posts",
        operation_summary="List Blog Posts",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of items per page", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response("List of blog posts", schema=BlogSerializer)
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Retrieve a specific blog post by ID",
        operation_summary="Get Blog Post",
        responses={
            200: openapi.Response("Blog post details", schema=BlogSerializer),
            404: "Not Found - Blog post not found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Update a blog post (partial update)",
        operation_summary="Update Blog Post",
        request_body=BlogSerializer,
        responses={
            200: openapi.Response("Updated blog post", schema=BlogSerializer),
            400: "Bad Request - Invalid data",
            403: "Forbidden - You can only modify your own blogs",
            404: "Not Found - Blog post not found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        blog = self.get_object()
        if blog.author != request.user:
            return Response({"error": "You can only modify your own blogs"}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete a blog post",
        operation_summary="Delete Blog Post",
        responses={
            200: "Blog deleted successfully",
            403: "Forbidden - You can only delete your own blogs",
            404: "Not Found - Blog post not found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        blog = self.get_object()
        if blog.author != request.user:
            return Response({"error": "You can only delete your own blogs"}, status=status.HTTP_403_FORBIDDEN)
        blog.delete()
        return Response({"message": "Blog deleted successfully"}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Get detailed blog information with latest comments and like count",
        operation_summary="Get Blog Details",
        responses={
            200: openapi.Response("Blog details with comments", schema=BlogDetailSerializer),
            404: "Not Found - Blog post not found"
        }
    )
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """
        Get detailed blog information including latest comments and like count.
        """
        blog = self.get_object()
        latest_comments = blog.comments.all().order_by('-created_at')[:COMMENTS_ON_DETAIL_BLOG]
        blog_data = BlogDetailSerializer(blog).data
        blog_data['latest_comments'] = CommentSerializer(latest_comments, many=True).data
        return Response(blog_data)
    
    @swagger_auto_schema(
        operation_description="Like a blog post",
        operation_summary="Like Blog Post",
        responses={
            200: "Blog liked",
            401: "Unauthorized - Authentication required",
            404: "Not Found - Blog post not found"
        }
    )
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        Like a blog post. Creates a like relationship if it doesn't exist.
        """
        blog = self.get_object()
        Like.objects.get_or_create(user=request.user, blog=blog)
        return Response({"message": "Blog liked"})
    
    @swagger_auto_schema(
        operation_description="Unlike a blog post",
        operation_summary="Unlike Blog Post",
        responses={
            200: "Blog unliked",
            401: "Unauthorized - Authentication required",
            404: "Not Found - Blog post not found"
        }
    )
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """
        Unlike a blog post. Removes the like relationship if it exists.
        """
        blog = self.get_object()
        Like.objects.filter(user=request.user, blog=blog).delete()
        return Response({"message": "Blog unliked"})
    
    @swagger_auto_schema(
        operation_description="Add a comment to a blog post",
        operation_summary="Comment on Blog Post",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['content'],
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Comment content")
            }
        ),
        responses={
            200: openapi.Response("Comment created", schema=CommentSerializer),
            400: "Bad Request - Invalid data",
            401: "Unauthorized - Authentication required",
            404: "Not Found - Blog post not found"
        }
    )
    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        """
        Add a comment to a blog post.
        """
        blog = self.get_object()
        comment = Comment.objects.create(
            user=request.user,
            blog=blog,
            content=request.data.get("content")
        )
        return Response(CommentSerializer(comment).data)
    
    @swagger_auto_schema(
        operation_description="Get all comments for a blog post with pagination",
        operation_summary="Get Blog Comments",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Number of comments per page", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response("Paginated list of comments", schema=CommentSerializer),
            404: "Not Found - Blog post not found"
        }
    )
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """
        Get all comments for a blog post with pagination support.
        """
        blog = self.get_object()
        comments = blog.comments.all().order_by('-created_at')
        paginator = CommentPagination()
        page = paginator.paginate_queryset(comments, request)
        if page is not None:
            serializer = CommentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)