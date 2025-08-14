from rest_framework import serializers
from .models import Blog, Like, Comment

class BlogSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = ['id', 'author', 'title', 'content', 'created_at', 'updated_at', 'likes_count', 'comments_count']
        read_only_fields = ['author']

    def get_likes_count(self, obj):
        return Like.objects.filter(blog=obj).count()

    def get_comments_count(self, obj):
        return Comment.objects.filter(blog=obj).count()


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at']
        read_only_fields = ['user']


class BlogDetailSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    latest_comments = serializers.SerializerMethodField()

    class Meta:
        model = Blog
        fields = [
            'id', 'author', 'title', 'content',
            'created_at', 'updated_at',
            'likes_count', 'comments_count', 'latest_comments'
        ]

    def get_likes_count(self, obj):
        return Like.objects.filter(blog=obj).count()

    def get_comments_count(self, obj):
        return Comment.objects.filter(blog=obj).count()

    def get_latest_comments(self, obj):
        latest = Comment.objects.filter(blog=obj).order_by('-created_at')[:5]
        return CommentSerializer(latest, many=True).data
