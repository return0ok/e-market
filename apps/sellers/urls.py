from django.urls import path

from apps.profiles.urls import urlpatterns
from apps.sellers.views import SellersView, SellerProductsView, SellerProductView, SellerOrdersView, \
    SellerOrderItemsView

urlpatterns = [
    path("", SellersView.as_view()),
    path("products/", SellerProductsView.as_view()),
    path("product/<slug:slug>/", SellerProductView.as_view()),
    path("orders/", SellerOrdersView.as_view()),
    path("orders/<str:tx_ref>/", SellerOrderItemsView.as_view()),
]