# Create your models here.
from django.db import models
import uuid
from django.core.exceptions import ValidationError
class Payment(models.Model):

    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Complted', 'Completed'),
        ('Failed', 'Failed'),
    ]
    user_id = models.IntegerField()  
    order = models.IntegerField()
    currency = models.CharField(max_length=10, default='USD')  # e.g., USD, EUR
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    order_signature = models.UUIDField()
    items = models.JSONField(default=list, blank=True)
    amount = models.IntegerField(default=1)
    transaction_id = models.UUIDField(
        default=uuid.uuid4,  # autogenerates new UUID
        editable=False,      # hide in Django admin so staff can’t change it
        unique=True          # ensures no duplicates
    )
    payment_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    payer_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} - {self.status}"
        
    
    def clean(self):
        # Enforce your business rule
        if self.status == 'Completed' and not self.payment_id:
            raise ValidationError({
                'payment_id': 'Completed payments must have a PayPal payment ID.'
            })
        
        if self.status == 'Completed' and not self.payer_id:
            raise ValidationError({
                'payer_id': 'Completed payments must have a payer ID.'
            })
    
    def save(self, *args, **kwargs):
        self.clean()  # Run validation before saving
        super().save(*args, **kwargs)
