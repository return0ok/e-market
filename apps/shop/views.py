from itertools import product
from venv import create

from django.core.serializers import serialize
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.response import Response
from rest_framework.utils.mediatypes import order_by_precedence
from rest_framework.views import APIView
from rest_framework import status
from unicodedata import category

from apps.common.permissions import IsAdminOrReadOnly, IsAuthenticatedOrReadOnly, IsOwner
from apps.common.utils import set_dict_attr
from apps.shop.serializers import CategorySerializer, ProductSerializer, ReviewSerializer
from rest_framework.pagination import PageNumberPagination

from apps.shop.models import Category, Product, Review
from apps.sellers.models import Seller
from apps.profiles.models import Order, OrderItem, ShippingAddress
from apps.shop.serializers import OrderItemSerializer, ToggleCartItemSerializer, \
                                    CheckoutSerializer, OrderSerializer
from apps.shop.filters import ProductFilter
from apps.shop.schema_examples import PRODUCT_PARAM_EXAMPLE
from apps.common.paginations import CustomPagination

tags=["Shop"]

class CategoriesView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    serializer_class = CategorySerializer
    @extend_schema(
        summary="Categories Fetch",
        description="""
                This endpoint returns all categories.
            """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        serializer = self.serializer_class(categories, many=True)
        return Response(data=serializer.data, status=200)


    @extend_schema(
        summary="Category Creating",
        description="""
                This endpoint creates categories.
            """,
        tags=tags
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            new_cat = Category.objects.create(**serializer.validated_data)
            serializer = self.serializer_class(new_cat)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)
        

class ProductsByCategoryView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="category_products",
        summary="Category Products Fetch",
        description="""
                This endpoint returns all products in a particular category.
            """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        category = Category.objects.get_or_none(slug=kwargs["slug"])
        if not category:
            return Response(data={"message": "Category does not exist!"}, status=404)
        products = Product.objects.select_related("category", "seller", "seller__user").filter(category=category)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)

class ProductsView_version_1(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="all_products",
        summary="Product Fetch",
        description="""
                This endpoint returns all products.
            """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.select_related("category", "seller", "seller__user").all()
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)

class ProductsView_version_2(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="all_products",
        summary="Product Fetch",
        description="""
                This endpoint returns all products.
            """,
        tags=tags,
        parameters=[
            OpenApiParameter(
                name="max_price",
                description="Filter products by MAX current price",
                required=False,
                type=OpenApiTypes.INT,
            ),
            OpenApiParameter(
                name="min_price",
                description="Filter products by MIN current price",
                required=False,
                type=OpenApiTypes.INT,
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.select_related("category", "seller", "seller__user").all()
        max_price = request.GET.get('max_price')
        min_price = request.GET.get('min_price')
        if max_price and min_price:
            if float(max_price) <= float(min_price):
                return Response(
                    data={"message": "The maximum price must be higher than the minimum"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        if max_price:
            products = products.filter(price_current__lte=max_price)
        if min_price:
            products = products.filter(price_current__gte=min_price)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)

class ProductsView(APIView):
    serializer_class = ProductSerializer
    pagination_class = CustomPagination
    @extend_schema(
        operation_id="all_products",
        summary="Product Fetch",
        description="""
                This endpoint returns all products.
            """,
        tags=tags,
        parameters=PRODUCT_PARAM_EXAMPLE,
    )
    def get(self, request, *args, **kwargs):
        products = Product.objects.select_related("category", "seller", "seller__user").all()
        filterset = ProductFilter(request.query_params, queryset=products)
        if filterset.is_valid():
            queryset = filterset.qs
            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serializer = self.serializer_class(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)
        else:
            return Response(filterset.errors, status=400)

class ProductsBySellerView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Seller Products Fetch",
        description="""
                This endpoint returns all products in a particular seller.
            """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(slug=kwargs["slug"])
        if not seller:
            return Response(data={"message": "Seller does not exist!"}, status=404)
        products = Product.objects.select_related("category", "seller", "seller__user").filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=200)

class ProductView(APIView):
    serializer_class = ProductSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        operation_id="product_detail",
        summary="Product Details Fetch",
        description="""
                This endpoint returns the details for a product via the slug.
            """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        product = self.get_object(kwargs["slug"])
        if not product:
            return Response(data={"message": "Product does not exist!"}, status=404)
        serializer = self.serializer_class(product)
        return Response(data=serializer.data, status=200)

class CartView(APIView):
    serializer_class = OrderItemSerializer

    @extend_schema(
        summary="Cart Items Fetch",
        description="""
                This endpoint returns all items in a user cart.
            """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        orderitems = OrderItem.objects.filter(user=user, order=None).select_related(
            "product", "product__seller", "product__seller__user")
        serializer = self.serializer_class(orderitems, many=True)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Toggle Item in cart",
        description="""
            This endpoint allows a user or guest to add/update/remove an item in cart.
            If quantity is 0, the item is removed from cart
        """,
        tags = tags,
        request=ToggleCartItemSerializer
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = ToggleCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        quantity = data["quantity"]

        product = Product.objects.select_related("seller", "seller__user").get_or_none(slug=data["slug"])
        if not product:
            return Response({"message": "No Product with that slug"}, status=404)
        orderitem, created = OrderItem.objects.update_or_create(
            user = user,
            order_id=None,
            product = product,
            defaults = {"quantity": quantity},
        )
        resp_message_substring = "Update In"
        status_code = 200
        if created:
            status_code = 201
            resp_message_substring = "Added To"
        if orderitem.quantity == 0:
            resp_message_substring = "Removed From"
            orderitem.delete()
            data = None
        if resp_message_substring != "Removed From":
            serializer = self.serializer_class(orderitem)
            data = serializer.data
        return Response(data={"message": f"Item {resp_message_substring} Cart", "item": data}, status=status_code)

class CheckoutView(APIView):
    serializer_class = CheckoutSerializer

    @extend_schema(
        summary="Checkout",
        description="""
                   This endpoint allows a user to create an order through which payment can then be made through.
                   """,
        tags=tags,
        request=CheckoutSerializer,
    )
    def post(self, request, *args, **kwargs):
        # Proceed to checkout
        user = request.user
        orderitems = OrderItem.objects.filter(user=user, order=None)
        if not orderitems.exists():
            return Response({"message": "No Items in Cart"}, status=404)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_id = data.get("shipping_id")
        if shipping_id:
            shipping = ShippingAddress.objects.get_or_none(id=shipping_id)
            if not shipping:
                return Response({"message": "No shipping address with that ID"}, status=404)

        fields_to_update = [
            "full_name",
            "email",
            "phone",
            "address",
            "city",
            "country",
            "zipcode",
        ]
        data = {}
        for field in fields_to_update:
            value = getattr(shipping, field)
            data[field] = value

        order = Order.objects.create(user=user, **data)
        orderitems.update(order=order)

        serializer = OrderSerializer(order)
        return Response(data={"message": "Checkout Successful", "item": serializer.data}, status=200)


class ReviewsProductView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = ReviewSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        operation_id="reviews_product_view",
        summary="Reviews Product Fetch",
        description="""
                    This endpoint returns all reviews for a product.
                """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        product = self.get_object(kwargs["slug"])
        reviews = Review.objects.filter(product=product)
        if not reviews:
            return Response(data={"message": "Reviews does not exist for this product!"}, status=404)
        serializer = self.serializer_class(reviews, many=True)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Review Items for one product",
        description="""
                    This endpoint returns all items in a user review product1.
                """,
        tags=tags,
        request=ReviewSerializer,
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        product = self.get_object(kwargs["slug"])
        review = Review.objects.get_or_none(user=user, product=product)
        if review:
            return Response(data={"message": "This product already has your review"}, status=200)
        else:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                data = serializer.validated_data
                new_review = Review.objects.create(user=user, product=product, **data)
                serializer = self.serializer_class(new_review)
                return Response(serializer.data, status=201)
            else:
                return Response(serializer.errors, status=400)

class ReviewUserProductView(APIView):
    permission_classes = [IsOwner]
    serializer_class = ReviewSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        operation_id="reviews_product_view",
        summary="ReviewUser for one Product Fetch",
        description="""
                        This endpoint returns all review-user for a product.
                    """,
        tags=tags
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        product = self.get_object(kwargs["slug"])
        review = Review.objects.get_or_none(user=user, product=product)
        if not review:
            return Response(data={"message": "Review does not exist!"}, status=404)
        serializer = self.serializer_class(review)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="ReviewUser Update",
        description="""
                        This endpoint allows a user to update his/her profile.
                    """,
        tags=tags,
        request={"multipart/form-data": serializer_class},
    )
    def put(self, request, *args, **kwargs):
        user = request.user
        product = self.get_object(kwargs["slug"])
        review = Review.objects.get_or_none(user=user, product=product)
        if not review:
            return Response(data={"message": "Review does not exist!"}, status=404)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        review = set_dict_attr(review, data)
        review.save()
        serializer = self.serializer_class(review)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Delete Review Product to slug",
        description="""
                        This endpoint allows a user to delete his/her product.
                    """,
        tags=tags,
    )
    def delete(self, request, *args, **kwargs):
        user = request.user
        product = self.get_object(kwargs["slug"])
        review = Review.objects.get_or_none(user=user, product=product)
        if not review:
            return Response(data={"message": "Review does not exist!"}, status=404)
        review.delete()
        return Response(data={"message": "Review deleted successfully"}, status=200)