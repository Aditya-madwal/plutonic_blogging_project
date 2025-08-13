from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
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
    
    # create blog api
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    # patch blog api
    def partial_update(self, request, *args, **kwargs):
        blog = self.get_object()
        if blog.author != request.user:
            return Response({"error": "You can only modify your own blogs"}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)
    
    # delete blog
    def destroy(self, request, *args, **kwargs):
        blog = self.get_object()
        if blog.author != request.user:
            return Response({"error": "You can only delete your own blogs"}, status=status.HTTP_403_FORBIDDEN)
        blog.delete()
        return Response({"message": "Blog deleted successfully"}, status=status.HTTP_200_OK)
    
    # detail blog api + 5 commetns + like count
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        blog = self.get_object()
        latest_comments = blog.comments.all().order_by('-created_at')[:COMMENTS_ON_DETAIL_BLOG]
        blog_data = BlogDetailSerializer(blog).data
        blog_data['latest_comments'] = CommentSerializer(latest_comments, many=True).data
        return Response(blog_data)
    
    # like blog
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        blog = self.get_object()
        Like.objects.get_or_create(user=request.user, blog=blog)
        return Response({"message": "Blog liked"})
    
    # unlike
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        blog = self.get_object()
        Like.objects.filter(user=request.user, blog=blog).delete()
        return Response({"message": "Blog unliked"})
    
    # comment on blog
    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        blog = self.get_object()
        comment = Comment.objects.create(
            user=request.user,
            blog=blog,
            content=request.data.get("content")
        )
        return Response(CommentSerializer(comment).data)
    
    # show comments
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        blog = self.get_object()
        comments = blog.comments.all().order_by('-created_at')
        paginator = CommentPagination()
        page = paginator.paginate_queryset(comments, request)
        if page is not None:
            serializer = CommentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)