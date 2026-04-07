from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("full_title", models.CharField(blank=True, max_length=500, null=True)),
                ("color", models.CharField(blank=True, max_length=100, null=True)),
                ("storage", models.CharField(blank=True, max_length=50, null=True)),
                (
                    "manufacturer",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "regular_price",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                ("sale_price", models.CharField(blank=True, max_length=50, null=True)),
                ("photos", models.JSONField(blank=True, null=True)),
                (
                    "product_code",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("reviews_count", models.IntegerField(blank=True, null=True)),
                (
                    "screen_diagonal",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                (
                    "screen_resolution",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("specifications", models.JSONField(blank=True, null=True)),
                (
                    "parser_type",
                    models.CharField(default="requests_bs4", max_length=20),
                ),
                ("parsed_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Product",
                "verbose_name_plural": "Products",
            },
        ),
    ]
