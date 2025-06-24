from django.urls import path

from apps.shop.views import CategoriesView, ProductsByCategoryView, ProductsView, ProductView, ProductsBySellerView, \
    CartView, CheckoutView, ReviewsProductView, ReviewUserProductView

urlpatterns = [
    path("categories/", CategoriesView.as_view()),
    path("categories/<slug:slug>/", ProductsByCategoryView.as_view()),
    path("sellers/<slug:slug>/", ProductsBySellerView.as_view()),
    path("products/", ProductsView.as_view()),
    path("products/<slug:slug>/", ProductView.as_view()),
    path("reviews/product/<slug:slug>/", ReviewsProductView.as_view()),
    path("review/product/<slug:slug>/", ReviewUserProductView.as_view()),
    path("cart/", CartView.as_view()),
    path("checkout/", CheckoutView.as_view()),

]