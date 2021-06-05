from django.db import models
from authentication.models import User


class Transaction(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, null=True)
    TRANSACTION = ((0, 'افزایش اعتبار'), (1, 'هزینه سنجش'))
    transactions_type = models.IntegerField(choices=TRANSACTION, default=1)
    description = models.TextField(blank=True, default='', null=True)
    total = models.DecimalField(max_digits=9, decimal_places=2, default='0.0')
    discount = models.DecimalField(max_digits=9, decimal_places=2, default='0.0')
    total_credit = models.DecimalField(max_digits=9, decimal_places=2, default='0.0')
    currency = models.CharField(max_length=10, default="تومان")
    wage = models.DecimalField(max_digits=9, decimal_places=2, default='0.0')
    gateway = models.CharField(max_length=20, null=True, blank=True)
    terminal = models.CharField(max_length=20, null=True, blank=True)
    pay_ref = models.CharField(max_length=200, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    pay_trace = models.CharField(max_length=100, null=True, blank=True)
    pay_pan = models.CharField(max_length=25, null=True, blank=True)
    pay_cid = models.CharField(max_length=300, null=True, blank=True)
    pay_time = models.DateTimeField(auto_now_add=True,null=True,blank=True)
