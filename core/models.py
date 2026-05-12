from django.db import models

class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="اسم الكورس")
    description = models.TextField(verbose_name="الوصف")
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="السعر")
    image = models.ImageField(upload_to='courses/', verbose_name="صورة الكورس")

    def __str__(self):
        return self.title