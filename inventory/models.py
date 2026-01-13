from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


# SKU Configuration for GrinkraWear
BRAND_CODE = 'GRK'

# Season Choices
SEASON_CHOICES = [
    ('SU', 'Summer'),
    ('WI', 'Winter'),
    ('SP', 'Spring'),
    ('FA', 'Fall'),
    ('AY', 'All Year'),
]

# Category Codes for SKU
CATEGORY_CODES = {
    'T-Shirt': 'TS',
    'Hoodie': 'HD',
    'Jacket': 'JK',
    'Shirt': 'SH',
    'Pants': 'PT',
    'Shorts': 'SR',
    'Sweater': 'SW',
    'Dress': 'DR',
    'Skirt': 'SK',
    'Coat': 'CT',
}

# Gender Choices
GENDER_CHOICES = [
    ('M', 'Men'),
    ('W', 'Women'),
    ('U', 'Unisex'),
]

# Color Choices
COLOR_CHOICES = [
    ('BK', 'Black'),
    ('WH', 'White'),
    ('RD', 'Red'),
    ('BL', 'Blue'),
    ('GR', 'Green'),
    ('GY', 'Grey'),
    ('NV', 'Navy'),
    ('PN', 'Pink'),
    ('YL', 'Yellow'),
    ('OR', 'Orange'),
    ('PR', 'Purple'),
    ('BR', 'Brown'),
    ('BG', 'Beige'),
    ('MR', 'Maroon'),
    ('TL', 'Teal'),
]

# Size Choices
SIZE_CHOICES = [
    ('XS', 'Extra Small'),
    ('S', 'Small'),
    ('M', 'Medium'),
    ('L', 'Large'),
    ('XL', 'Extra Large'),
    ('XXL', 'Double XL'),
    ('XXXL', 'Triple XL'),
    ('FS', 'Free Size'),
]


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(
        max_length=3,
        unique=True,
        blank=True,
        default='',
        help_text='2-3 letter code for SKU generation (e.g., TS for T-Shirt)'
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def product_count(self):
        return self.products.count()

    def save(self, *args, **kwargs):
        # Auto-generate code from predefined mapping or name
        if not self.code:
            self.code = CATEGORY_CODES.get(self.name, self.name[:2].upper())
        super().save(*args, **kwargs)


class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='SKU',
        blank=True,
        help_text='Auto-generated. Format: GRK-SEASON-CATEGORY-GENDER-COLOR-SIZE-SERIAL'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )

    # Clothing-specific fields for SKU generation
    season = models.CharField(
        max_length=2,
        choices=SEASON_CHOICES,
        default='AY',
        help_text='Season collection'
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default='U',
        help_text='Target gender'
    )
    color = models.CharField(
        max_length=2,
        choices=COLOR_CHOICES,
        default='BK',
        help_text='Primary color'
    )
    size = models.CharField(
        max_length=4,
        choices=SIZE_CHOICES,
        default='M',
        help_text='Size'
    )

    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
        help_text='Cost price for profit calculation'
    )
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text='Alert when stock falls below this level'
    )
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def generate_sku(self):
        """
        Generate SKU in format: GRK-SEASON-CATEGORY-GENDER-COLOR-SIZE-SERIAL
        Example: GRK-SU-TS-M-RD-M-001
        """
        # Get category code
        cat_code = self.category.code if self.category else 'XX'

        # Get the next serial number for this combination
        serial = self._get_next_serial()

        # Build SKU
        sku_parts = [
            BRAND_CODE,           # GRK
            self.season,          # SU, WI, etc.
            cat_code,             # TS, HD, etc.
            self.gender,          # M, W, U
            self.color,           # BK, WH, etc.
            self.size,            # S, M, L, etc.
            f'{serial:03d}'       # 001, 002, etc.
        ]

        return '-'.join(sku_parts)

    def _get_next_serial(self):
        """Get next serial number for this product combination."""
        # Find products with same attributes (excluding serial)
        prefix = f"{BRAND_CODE}-{self.season}-"
        if self.category:
            prefix += f"{self.category.code}-"
        else:
            prefix += "XX-"
        prefix += f"{self.gender}-{self.color}-{self.size}-"

        # Find highest existing serial with this prefix
        existing = Product.objects.filter(
            sku__startswith=prefix
        ).exclude(pk=self.pk)

        if not existing.exists():
            return 1

        # Extract serial numbers and find max
        max_serial = 0
        for product in existing:
            try:
                serial_str = product.sku.split('-')[-1]
                serial = int(serial_str)
                if serial > max_serial:
                    max_serial = serial
            except (ValueError, IndexError):
                continue

        return max_serial + 1

    def save(self, *args, **kwargs):
        # Auto-generate SKU only on creation (when no SKU exists)
        if not self.sku:
            # Need to save first to get pk if category needs it
            self.sku = self.generate_sku()
        super().save(*args, **kwargs)

    @property
    def stock_status(self):
        if self.quantity == 0:
            return 'out_of_stock'
        elif self.quantity <= self.low_stock_threshold:
            return 'low_stock'
        return 'in_stock'

    @property
    def stock_status_display(self):
        status_map = {
            'out_of_stock': 'Out of Stock',
            'low_stock': 'Low Stock',
            'in_stock': 'In Stock'
        }
        return status_map.get(self.stock_status, 'Unknown')

    @property
    def profit_margin(self):
        if self.cost_price and self.cost_price > 0:
            return ((self.price - self.cost_price) / self.price) * 100
        return None

    def adjust_stock(self, quantity_change, reason=''):
        """Adjust stock quantity. Positive for additions, negative for deductions."""
        new_quantity = self.quantity + quantity_change
        if new_quantity < 0:
            raise ValueError('Insufficient stock')
        self.quantity = new_quantity
        self.save()
        return self.quantity
