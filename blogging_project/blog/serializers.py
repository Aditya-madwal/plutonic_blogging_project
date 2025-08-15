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

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return Blog.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at']
        read_only_fields = ['user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return Comment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'
        read_only_fields = ['user']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return Like.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


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
