
from .models import Notification 

def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(item['quantity'] for item in cart.values())
    return {'cart_count': count}

def notification_count(request):
    count = 0

    if request.user.is_authenticated:
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return {'notif_count': count}