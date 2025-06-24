from django.db import models
from autoslug import AutoSlugField

# from apps.common.managers import IsDeletedQuerySet
from apps.common.models import BaseModel, IsDeletedModel
from apps.sellers.models import Seller
from apps.accounts.models import User


# Create your models here.

RATING_CHOICES = (
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5)
)

class Category(BaseModel):
    """
        Represents a product category.

        Attributes:
            name (str): The category name, unique for each instance.
            slug (str): The slug generated from the name, used in URLs.
            image (ImageField): An image representing the category.

        Methods:
            __str__():
                Returns the string representation of the category name.
    """

    name = models.CharField(max_length=100, unique=True)
    slug = AutoSlugField(populate_from="name", unique=True, always_update=True)
    image = models.ImageField(upload_to='category_images/')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Product(IsDeletedModel):
    """
        Represents a product listed for sale.

        Attributes:
            seller (ForeignKey): The user who is selling the product.
            name (str): The name of the product.
            slug (str): The slug generated from the name, used in URLs.
            desc (str): A description of the product.
            price_old (Decimal): The original price of the product.
            price_current (Decimal): The current price of the product.
            category (ForeignKey): The category to which the product belongs.
            in_stock (int): The quantity of the product in stock.
            image1 (ImageField): The first image of the product.
            image2 (ImageField): The second image of the product.
            image3 (ImageField): The third image of the product.
        """
    seller = models.ForeignKey(Seller, on_delete=models.SET_NULL, related_name="products", null=True)
    name = models.CharField(max_length=100)
    slug = AutoSlugField(populate_from="name", unique=True, db_index=True)
    desc = models.TextField()
    price_old = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    price_current = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    in_stock = models.IntegerField(default=5)

    # Only 3 images are allowed
    image1 = models.ImageField(upload_to='product_images/')
    image2 = models.ImageField(upload_to='product_images/', blank=True)
    image3 = models.ImageField(upload_to='product_images/', blank=True)

    def __str__(self):
        return str(self.name)


class Review(IsDeletedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="review_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="review_products")
    rating = models.PositiveIntegerField(default=0, choices=RATING_CHOICES)
    text = models.TextField()

