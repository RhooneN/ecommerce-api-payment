import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def update_order_status(auth_header, signature, new_status, notes=""):
    print("auth_header=", auth_header)
    """
    Update order status in the order service.

    Args:
        signature (str): Unique order identifier (transaction_id, uuid, etc.)
        new_status (str): New status value (e.g., 'confirmed', 'failed').
        notes (str): Optional notes for status update.

    Returns:
        bool: True if update succeeded, False otherwise.
    """
    order_service_url = getattr(settings, 'ORDER_SERVICE_URL', 'http://localhost:8003')
    url = f"{order_service_url}/orders/{signature}/status/"

    headers = {'Content-Type': 'application/json'}
    if auth_header:
        headers['Authorization'] = auth_header
        print("auth", headers['Authorization'])
        
    auth_token = getattr(settings, 'ORDER_SERVICE_TOKEN', None)
    if auth_token:
        headers['Authorization'] = f'Bearer {auth_token}'

    payload = {
        "status": new_status,
        "notes": notes,
    }

    try:
        response = requests.patch(
            url,
            json=payload,
            headers=headers,
            timeout=(2, 5)  # connect timeout=2s, read timeout=5s
        )

        if response.status_code in (200, 204):
            logger.info(f"[OrderUpdate] Order {signature} -> {new_status}")
            return True
        else:
            logger.error(
                f"[OrderUpdate] Failed ({response.status_code}): "
                f"Order {signature}, payload={payload}, response={response.text}"
            )
            return False

    except requests.exceptions.RequestException as e:
        logger.exception(f"[OrderUpdate] Exception for order {signature}: {e}")
        return False
