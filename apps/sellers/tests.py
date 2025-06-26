from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIRequestFactory
from rest_framework import status

from apps.sellers.views import SellerProductsView
from apps.shop.models import Product


# Create your tests here.

class SellerProductsViewTests(TestCase):
    print("TEST-START")
    def setUp(self):
        self.factory = APIRequestFactory()
        # self.product1 = Product.objects.create()

    def test_get_list(self):
        url = reverse("sellers/products")
        request = self.factory.get(url)
        view = SellerProductsView.as_view({'get': 'list'})
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    # def test_post_create(self):
    #     url = reverse("sellers/products")
    #     data = {"title": "New Book", "author": "New Author"}