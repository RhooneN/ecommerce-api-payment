from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            self.fields['order'].queryset = Order.objects.filter(user_id=request.user.user_id)


class UPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'user_id', 'order', 'currency', 'order_signature', 'status', 'transaction_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user_id', 'transaction_id', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            self.fields['order'].queryset = Order.objects.filter(user_id=request.user.user_id)
            
