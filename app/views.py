# views.py
import requests
import logging
from decimal import Decimal
from django.conf import settings
from django.http import HttpResponseRedirect
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from shared.simple_permissions import IsAuth, IsAuthenticatedOrReadOnly, IsAdmin
from paypal.standard.forms import PayPalPaymentsForm
from paypalrestsdk import Payment as PPayment
from .models import Payment
from .serializers import PaymentSerializer
from .utils import update_order_status
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status": "ok"})
logger = logging.getLogger(__name__)

class PaymentView(APIView):
    permission_classes = [IsAuth]
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.auth_header = self.request.headers.get("Authorization")
        
    def get(self, request):
        """Get user's payment history"""
        user_id = self.request.user.user_id
        payments = Payment.objects.filter(user_id = user_id)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    @transaction.atomic
    def post(self, request):
        """Create a new payment from an order"""
        try:
            order_id = request.data.get("order_id")
            print(order_id)
            if not order_id:
                return Response(
                    {"error": "order_id is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(f"Processing payment for order: {order_id}")
            
            # . Fetch order details from order service
            user_id = self.request.user.user_id
            order_data = self._fetch_order_details(order_id, user_id)
            if not order_data:
                return Response(
                    {"error": "Order not found or not accessible"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 3. Validate order is in correct state
            if order_data.get('status') not in ['Pending', 'Confirmed']:
                return Response(
                    {"error": f"Order cannot be paid. Current status: {order_data.get('status')}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 4. Create Django Payment record
            payment_data = {
                'order': order_id,
                'amount': order_data.get('total'),
                'user_id': user_id,
                'currency': request.data.get('currency', 'USD'),
                'order_signature':order_data.get('signature'),
                'payment_method': request.data.get('payment_method', 'paypal'),
                'status': 'Pending'
            }
            serializer = PaymentSerializer(data=payment_data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            payment = serializer.save()
       
            # 5. Update order status to "processing"
            signature = order_data.get('signature')
            update_order_status(self.auth_header, signature, 'Processing', "Payment initiated")
            
            # 6. Create PayPal Payment
            ppayment_result = self._create_paypal_payment(payment, order_data)
            
            if ppayment_result['success']:
                payment.status = 'Processing'
                payment.payment_id = ppayment_result['payment_id']
                payment.save()
                
                # Update order status
                update_order_status(self.auth_header, signature, 'Processing', "Payment Processing")
                return Response({
                    'success': True,
                    'payment_id': payment.id,
                    'paypal_payment_id': payment.payment_id,
                    'approval_url': ppayment_result['approval_url']
                })
            else:
                # Payment creation failed
                payment.status = 'Failed'
                payment.save()
                
                # Update order status back to pending
                update_order_status(self.auth_header, signature, 'Pending', f"Payment failed: {ppayment_result.get('error')}")
                
                return Response({
                    'success': False,
                    'error': ppayment_result.get('error', 'Payment creation failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Payment creation error: {str(e)}")
            return Response(
                {"error": "Internal server error during payment creation"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _fetch_order_details(self, order_id, user_id):
        """Fetch order details from  service"""
        try: 
            order_service_url = getattr(settings, 'ORDER_SERVICE_URL', 'http://localhost:8003')
            url = f"{order_service_url}/orders/{order_id}/"
            
            headers = {'Content-Type': 'application/json'}
            if self.auth_header:
                 headers['Authorization'] = self.auth_header
            
            auth_token = getattr(settings, 'ORDER_SERVICE_TOKEN', None)
            if auth_token:
                headers['Authorization'] = f'Bearer {auth_token}'
            
            response = requests.get(
                url, 
                headers=headers,
                timeout=(2, 10)  # 2s connect, 10s read timeout
            )
            
            if response.status_code == 200:
                order_data = response.json()
           
                # Validate order belongs to the user
                if str(order_data['user_id']) != user_id:
                     logger.error(f"Failed to fetch order {order_id} because of ownership : HTTP {status.HTTP_404_NOT_FOUND}")
                     return None
                return order_data
            else:
                logger.error(f"Failed to fetch order {order_id}: HTTP {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching order {order_id}: {str(e)}")
            return None
    
    
    def _create_paypal_payment(self, payment, order_data):
        """Create PayPal payment"""
        try:
            # Build item list from order data
            item_list = {
                "items": []
            }
            
            for item in order_data.get('items', []):
                item_list["items"].append({
                    "name": item.get('product_id', f"Product {item.get('product_id')}"),
                    "sku": str(item.get('product_id')),
                    "price": str(item.get('price')),
                    "currency": payment.currency,
                    "quantity": item.get('quantity')
                })
            
            # Create PayPal payment
            ppayment = PPayment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": f"{settings.BASE_URL}/payment/execute/",
                    "cancel_url": f"{settings.BASE_URL}/payment/cancel/"
                },
                "transactions": [{
                    "item_list": item_list,
                    "amount": {
                        "total": str(payment.amount),
                        "currency": payment.currency
                    },
                    "description": f"Order #{order_data.get('signature', payment.order)}"
                }]
            })
            
            if ppayment.create():
                # Find approval URL
                approval_url = None
                for link in ppayment.links:
                    if link.rel == "approval_url":
                        approval_url = link.href
                        break
                
                return {
                    'success': True,
                    'payment_id': ppayment.id,
                    'approval_url': approval_url
                }
            else:
                logger.error(f"PayPal payment creation failed: {ppayment.error}")
                return {
                    'success': False,
                    'error': str(ppayment.error)
                }
                
        except Exception as e:
            logger.error(f"Error creating PayPal payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

class PaymentExecuteView(APIView):
    permission_classes = [IsAuth]
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.auth_header = self.request.headers.get("Authorization")

        
    def get(self, request):
        """Handle PayPal payment execution after user approval"""
        payment_id = request.GET.get('paymentId')
        payer_id = request.GET.get('PayerID')
        
        if not payment_id or not payer_id:
            return Response(
                {"error": "Missing PayPal payment parameters"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user_id = self.request.user.user_id
            # Get local payment record
            payment = Payment.objects.get(
                payment_id=payment_id, 
                user_id=user_id,
                status='Processing'
            )
            
            # Execute PayPal payment
            ppayment = PPayment.find(payment_id)
            
            if ppayment.execute({"payer_id": payer_id}):
                payment.payer_id = payer_id
                payment.status = 'Completed'
                payment.save()
                
                # Update order status to confirmed
                update_order_status(self.auth_header, 
                    payment.order_signature,
                    "Confirmed",
                    "Payment completed successfully"
                )
                
                return Response({
                    'success': True,
                    'message': 'Payment completed successfully',
                    'payment_id': payment.id
                })
            else:
                payment.status = 'Failed'
                payment.save()
                
                # Update order status back to pending
                update_order_status(self.auth_header, 
                    payment.order_signature,
                    "Pending",
                    "Payment not completed successfully"
                )
                
                return Response({
                    'success': False,
                    'error': 'Payment execution failed'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Payment.DoesNotExist:
            return Response(
                {"error": "Payment not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Payment execution error: {str(e)}")
            return Response(
                {"error": "Payment execution failed"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class PaymentCancelView(APIView):
    permission_classes = [IsAuth]
    
    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.auth_header = self.request.headers.get("Authorization")
        
    def get(self, request):
        """Handle PayPal payment cancellation"""
        payment_id = request.GET.get('paymentId')
        
        if payment_id:
            try:
                payment = Payment.objects.get(
                    payment_id=payment_id, 
                    user_id=request.user.user_id,
                    status='Processing'
                )
                payment.status = 'Failed'
                payment.save()
                
                # Update order status back to pending
                update_order_status(self.auth_header, payment.order_signature, 'Pending', "Payment cancelled by user")
                
            except Payment.DoesNotExist:
                pass
        
        return Response({
            'success': False,
            'message': 'Payment was cancelled'
        })
    
