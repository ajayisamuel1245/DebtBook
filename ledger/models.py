from django.db import models

# Create your models here.
import uuid
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone


class TraderProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.business_name


class Customer(models.Model):
    trader = models.ForeignKey(TraderProfile, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    notes = models.CharField(max_length=255, blank=True)
    statement_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def balance(self):
        credit = self.entries.filter(entry_type='credit').aggregate(t=Sum('amount'))['t'] or 0
        payment = self.entries.filter(entry_type='payment').aggregate(t=Sum('amount'))['t'] or 0
        return credit - payment

    def __str__(self):
        return self.name


class LedgerEntry(models.Model):
    ENTRY_TYPES = [
        ('credit', 'Credit Given'),
        ('payment', 'Payment Received'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='entries')
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.get_entry_type_display()} - {self.amount} ({self.customer.name})"