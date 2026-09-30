from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import TraderProfile, Customer, LedgerEntry

admin.site.register(TraderProfile)
admin.site.register(Customer)
admin.site.register(LedgerEntry)