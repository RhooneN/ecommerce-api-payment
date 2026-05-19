from django.test import TestCase
from rest_framework.test import APITestCase
from unittest.mock import patch
from django.urls import reverse
from .models import Payment
import paypalrestsdk
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
# ~ from .utils import update_order_status
import jwt
from django.conf import settings
from datetime import datetime, timedelta

def make_token(user):
    payload = {
        "user_id": user.id,
        "username": user.username,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

class PayPalPaymentTestCase(APITestCase):
    """ My authenticte func based on refreshtoken wasnt working well so i swiched to a fit-or
    you'll need to define 2 differents token for simple user and admin in environ
    """
	
    def authenticate(self, user):
        token = make_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def setUp(self):
        """
        Set up a test user and a sample order.
        """
       
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.login(username="testuser", password="testpass")
        patcher_fetch = patch("app.views.PaymentView._fetch_order_details")
        patcher_create = patch("app.views.PaymentView._create_paypal_payment")
        self.mock_fetch = patcher_fetch.start()
        self.mock_create = patcher_create.start()
        self.addCleanup(patcher_fetch.stop)
        self.addCleanup(patcher_create.stop)
        self.payment = Payment.objects.create(payment_id='PAYID-TEST123',
                order=1,
                order_signature='ff5a1af1-de95-46ca-a341-289089ae1f77',	
                user_id=self.user.id,
                status='Processing')
    @patch("app.views.update_order_status")
    @patch("app.views.PaymentView._fetch_order_details")
    @patch("app.views.PaymentView._create_paypal_payment")
    def test_create_payment_success(self, mock_create, mock_fetch, mock_status):
        """
        Test successful PayPal payment creation.
        """	
        self.authenticate(self.user)
        data = {'order_id': 1, 'currency': 'EUR', 'status': 'Pending'}
        user_id =  1
        mock_fetch.return_value ={'total': 144,
                'signature': 'ff5a1af1-de95-46ca-a341-289089ae1f77',
                'status': 'Pending'
            }
        mock_status.return_value = True
        mock_create.return_value = {'success': True, "payment_id": "PAY-12345",
        "approval_url": "https://paypal.com/approve/12345"}  # Simulate successful API call
        response = self.client.post(reverse('payment'), data, format='json')
        self.assertIn("approval_url", response.json())
        self.assertEqual(response.status_code, 200)  # Expecting redirect to PayPal approval URL
    @patch("app.views.update_order_status")
    @patch("paypalrestsdk.Payment.find")
    @patch("paypalrestsdk.Payment.execute")
    def test_execute_payment_success(self, mock_execute, mock_find, mock_status):
        """
        Test successful execution of a PayPal payment.
        """
        self.authenticate(self.user)
        mock_find.return_value = paypalrestsdk.Payment({"id": "PAYID-TEST123"})
        mock_execute.return_value = True  # Simulate successful execution
        mock_status.return_value = True
        url = reverse("execute-payment")
        response = self.client.get(url, {"paymentId": "PAYID-TEST123", "PayerID": "PAYER123"})
        # ~ print('response', response, response.json())

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
    @patch("app.views.update_order_status")
    @patch("app.views.PaymentView._fetch_order_details")
    @patch("app.views.PaymentView._create_paypal_payment")
    def test_create_payment_failure_paypal(self, mock_create, mock_fetch, mock_status):
        """
        Test failed PayPal payment creation.
        """
        self.authenticate(self.user)
        data = {'order_id': 1, 'currency': 'EUR', 'status': 'Pending'}
        user_id =  1
        mock_fetch.return_value ={'total': 144,
                'signature': 'ff5a1af1-de95-46ca-a341-289089ae1f77',
                'status': 'Pending'
            }
        mock_status.return_value = True
        mock_create.return_value = {'success': False, "payment_id": "PAY-12345",
        "approval_url": "https://paypal.com/approve/12345"}  # Simulate successful API call
        response = self.client.post(reverse('payment'), data, format='json')
        print('response', response, response.json())
        self.assertFalse(response.json()["success"])
        self.assertEqual(response.status_code, 400)  # Expecting redirect to PayPal approval URL
     
    @patch("app.views.update_order_status")
    @patch("app.views.PaymentView._fetch_order_details")
    @patch("app.views.PaymentView._create_paypal_payment")
    def test_create_payment_failure_with_bad_status(self, mock_create, mock_fetch, mock_status):
        """
        Test failed PayPal payment creation.
        """
        self.authenticate(self.user)
        data = {'order_id': 1, 'currency': 'EUR', 'status': 'Pending'}
        user_id =  1
        mock_status.return_value = True
        mock_fetch.return_value ={'total': 144,
                'signature': 'ff5a1af1-de95-46ca-a341-289089ae1f77',
                'status': 'Processing'
            }
        mock_create.return_value = {'success': True, "payment_id": "PAY-12345",
        "approval_url": "https://paypal.com/approve/12345"}  # Simulate successful API call
        response = self.client.post(reverse('payment'), data, format='json')
        print('response2', response, response.json())
        self.assertIn("error", response.json())
        self.assertEqual(response.status_code, 400)  # Expecting redirect to PayPal approval URL
    
    @patch("app.views.update_order_status")
    @patch("paypalrestsdk.Payment.find")
    @patch("paypalrestsdk.Payment.execute")
    def test_execute_payment_failure(self, mock_execute, mock_find, mock_status):
        """
        Test failed execution of a PayPal payment.
        """
        self.authenticate(self.user)
        mock_find.return_value = paypalrestsdk.Payment({"id": "PAYID-TEST123"})
        mock_execute.return_value = False
        mock_execute.error = {"message": "Execution error"}
        mock_status.return_value = True

        url = reverse("execute-payment")
        response = self.client.get(url, {"paymentId": "PAYID-TEST123", "PayerID": "PAYER123"})
        # ~ print('response2', response, response.json())

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

