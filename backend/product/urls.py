"""product app URL'lari — bazasi: /api/v1/"""

from django.urls import path

from .views import CategoryListView, ProductListView

app_name = 'product'

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('products/', ProductListView.as_view(), name='product-list'),
]
