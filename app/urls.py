from django.urls import path
from . import views
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('payment/', views.PaymentView.as_view(), name='payment'),
    path('payment/execute/', views.PaymentExecuteView.as_view(), name='execute-payment'),
    path('payment/cancel/', views.PaymentCancelView.as_view(), name='payment-cancel'),
    path("order_updater/", views.update_order_status, name='order-update'),
    path("health/", views.health),
    
    #Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
