from django.contrib import admin

# Register your models here.
from payment.models import Transaction

admin.site.register(Transaction)
