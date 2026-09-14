"""product app serializerlari."""

from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    """GET /api/v1/categories/ — kategoriya ro'yxati elementi."""

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'image', 'parent')
        read_only_fields = fields
