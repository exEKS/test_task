from django.db import models


class Product(models.Model):
    full_title = models.CharField(max_length=500, null=True, blank=True)
    color = models.CharField(max_length=100, null=True, blank=True)
    storage = models.CharField(max_length=50, null=True, blank=True)
    manufacturer = models.CharField(max_length=100, null=True, blank=True)

    regular_price = models.CharField(max_length=50, null=True, blank=True)
    sale_price = models.CharField(max_length=50, null=True, blank=True)

    photos = models.JSONField(null=True, blank=True)

    product_code = models.CharField(max_length=100, null=True, blank=True)
    reviews_count = models.IntegerField(null=True, blank=True)

    screen_diagonal = models.CharField(max_length=50, null=True, blank=True)
    screen_resolution = models.CharField(max_length=100, null=True, blank=True)

    specifications = models.JSONField(null=True, blank=True)

    parser_type = models.CharField(max_length=20, default="requests_bs4")
    parsed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_title or "Product"

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
