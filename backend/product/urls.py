"""product app URL'lari — bazasi: /api/v1/"""

from django.urls import path

from .views import CategoryListView, ProductListCreateView

app_name = 'product'

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('products/', ProductListCreateView.as_view(), name='product-list'),
]
