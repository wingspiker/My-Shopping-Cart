from django.contrib import admin
from .models import Product
from .models import Contact
from .models import Orders,orderUpdate

# Register your models here.
admin.site.register(Product)
admin.site.register(Contact)
admin.site.register(Orders)
admin.site.register(orderUpdate)