from django.core.serializers import serialize
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from unicodedata import category

from apps.common.permissions import IsSeller
from apps.common.utils import set_dict_attr
from apps.sellers.models import Seller
from apps.sellers.serializers import SellerSerializer

from apps.shop.models import Category, Product
from apps.shop.serializers import ProductSerializer, CreateProductSerializer, CheckItemOrderSerializer
from apps.profiles.models import Order, OrderItem
from apps.shop.serializers import ProductSerializer, CreateProductSerializer, OrderSerializer, \
        CheckItemOrderSerializer

tags = ["Sellers"]

class SellersView(APIView):
    serializer_class = SellerSerializer

    @extend_schema(
        summary="Apply to become a seller",
        description="""
                This endpoint allows a buyer to apply to become a seller.
            """,
        tags=tags)

    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data, partial=False)
        if serializer.is_valid():
            data = serializer.validated_data
            seller, _ = Seller.objects.update_or_create(user=user, defaults=data)
            user.account_type = 'SELLER'
            user.save()
            serializer = self.serializer_class(seller)
            return Response(data=serializer.data, status=201)
        else:
            return Response(data=serializer.errors, status=400)

class SellerProductsView(APIView):
    permission_classes = [IsSeller]
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Seller Products Fetch",
        description="""
                This endpoint returns all products from a seller.
                Products can be filtered by name, sizes or colors.
            """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response(data={"message": "Access is denied"}, status=403)
        products = Product.objects.select_related("category", "seller", "seller__user").filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Create a product",
        description="""
                This endpoint allows a seller to create a product.
            """,
        tags=tags,
        request=CreateProductSerializer,
        responses=CreateProductSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = CreateProductSerializer(data=request.data)
        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response(data={"message": "Access is denied"}, status=403)
        if serializer.is_valid():
            data = serializer.validated_data
            category_slug = data.pop("category_slug", None)
            category = Category.objects.get_or_none(slug=category_slug)
            if not category:
                return Response(data={"message": "Category does not exist!"}, status=404)
            data['category'] = category
            data['seller'] = seller
            new_prod = Product.objects.create(**data)
            serializer = self.serializer_class(new_prod)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)


class SellerProductView(APIView):
    permission_classes = [IsSeller]
    serializer_class = CreateProductSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        summary="Product Fetch Slug",
        description="""
                    This endpoint returns a single shipping address associated with a user.
                """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        product = self.get_object(kwargs["slug"])
        if not product:
            return Response(data={"message": "Product does not exist!"}, status=404)
        if product.seller.user != user:
            return Response(data={"message": "User does not permission for edite!"}, status=403)
        return Response(data=ProductSerializer(product).data, status=200)

    @extend_schema(
        summary="Seller Products Update",
        description="""
                    This endpoint allows a user to update his/her profile.
                """,
        tags=tags,
        request={"multipart/form-data": serializer_class},
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        product = self.get_object( kwargs["slug"])
        if not product:
            return Response(data={"message": "Product does not exist!"}, status=404)
        elif product.seller.user != user:
            return Response(data={"message": "User does not permission for edite!"}, status=403)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if str(product.price_current) != str(request.data["price_current"]):
            product.price_old = product.price_current

        product = set_dict_attr(product, data)
        product.save()
        serializer = self.serializer_class(product)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Delete Product to slug",
        description="""
                    This endpoint allows a user to delete his/her product.
                """,
        tags=tags,
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        product = self.get_object(kwargs["slug"])
        if not product:
            return Response(data={"message": "Product does not exist!"}, status=404)
        elif product.seller.user != user:
            return Response(data={"message": "User does not permission for edite!"}, status=403)

        product.delete()
        return Response(data={"message": "Product deleted successfully"}, status=200)

    
class SellerOrdersView(APIView):
    permission_classes = [IsSeller]
    serializer_class = OrderSerializer

    @extend_schema(
        operation_id="seller_orders_view",
        summary="Seller Orders Fetch",
        description="""
                This endpoint returns all orders for a particular seller.
            """,
        tags=tags
    )
    def get(self, request):
        seller = request.user.seller
        orders = (
            Order.objects.filter(orderitems__product__seller=seller).order_by("-create_at")
        )
        serializer = self.serializer_class(orders, many=True)
        return Response(data=serializer.data, status=200)

class SellerOrderItemsView(APIView):
    permission_classes = [IsSeller]
    serializer_class = CheckItemOrderSerializer

    @extend_schema(
        operation_id="seller_order_items_view",
        summary="Seller Items Order Fetch",
        description="""
                This endpoint returns all items order for a particular seller.
            """,
        tags=tags,

    )
    def get(self, request, **kwargs):
        seller = request.user.seller
        order = Order.objects.get_or_none(tx_ref=kwargs["tx_ref"])
        if not order:
            return Response(data={"message": "Order does not exist!"}, status=404)
        order_items = OrderItem.objects.filter(order=order, product__seller=seller)
        serializer = self.serializer_class(order_items, many=True)
        return Response(data=serializer.data, status=200)
