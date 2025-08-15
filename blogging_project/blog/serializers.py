from rest_framework import serializers
from .models import Blog, Like, Comment

class BlogSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Blog
        fields = ['id', 'author', 'title', 'content', 'created_at', 'updated_at', 'likes_count', 'comments_count', 'created_by']
        read_only_fields = ['author', 'created_by']

    def get_likes_count(self, obj):
        return Like.objects.filter(blog=obj).count()

    def get_comments_count(self, obj):
        return Comment.objects.filter(blog=obj).count()

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        validated_data['created_by'] = self.context['request'].user.created_by
        return Blog.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'content', 'created_at', 'created_by']
        read_only_fields = ['user', 'created_by']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['created_by'] = self.context['request'].user.created_by
        validated_data['blog'] = self.context['blog']
        return Comment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class LikeSerializer(serializers.ModelSerializer):
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Like
        fields = '__all__'
        read_only_fields = ['user', 'created_by']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['created_by'] = self.context['request'].user.created_by
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
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Blog
        fields = [
            'id', 'author', 'title', 'content',
            'created_at', 'updated_at',
            'likes_count', 'comments_count', 'latest_comments', 'created_by'
        ]

    def get_likes_count(self, obj):
        return Like.objects.filter(blog=obj).count()

    def get_comments_count(self, obj):
        return Comment.objects.filter(blog=obj).count()

    def get_latest_comments(self, obj):
        latest = Comment.objects.filter(blog=obj).order_by('-created_at')[:5]
        return CommentSerializer(latest, many=True).data
