from io import BytesIO
from PIL import Image
from django.core.files import File
from django.db import models
from vendor.models import Vendor, Preference
from django.utils.text import slugify





class Category(models.Model):
    title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=55)
    ordering = models.IntegerField(default=0)

    class Meta:
        ordering = ['ordering']

    def __str__(self):
        return self.title



class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, related_name="products", on_delete=models.CASCADE)

    title = models.CharField(max_length=50)
    slug = models.SlugField(max_length=55, blank=True, unique=True)
    description = models.TextField(blank=True, null=True)

    price = models.IntegerField()
    added_date = models.DateTimeField(auto_now_add=True)

    image = models.ImageField(upload_to='uploads/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='uploads/', blank=True, null=True)

    # 🟢 Preferencias alimentarias
    preferences = models.ManyToManyField(Preference, blank=True)

    class Meta:
        ordering = ['-added_date']

    def __str__(self):
        return self.title

    # ----------------------------
    # 🔥 GENERACIÓN AUTOMÁTICA SLUG
    # ----------------------------
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            num = 1

            # Evita slug duplicados
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{num}"
                num += 1

            self.slug = slug

        super().save(*args, **kwargs)

    # ----------------------------
    # 📸 THUMBNAIL
    # ----------------------------
    def get_thumbnail(self):
        if self.thumbnail:
            return self.thumbnail.url

        elif self.image:
            self.thumbnail = self.make_thumbnail(self.image)
            self.save()
            return self.thumbnail.url

        return "https://via.placeholder.com/240x180.jpg"

    def make_thumbnail(self, image, size=(300, 200)):
        img = Image.open(image)
        img.convert('RGB')
        img.thumbnail(size)

        thumb_io = BytesIO()
        img.save(thumb_io, "JPEG", quality=85)

        thumbnail = File(thumb_io, name=image.name)
        return thumbnail
