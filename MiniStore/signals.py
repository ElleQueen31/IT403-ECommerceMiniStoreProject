from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderItem, Notification, Product

# 1. Notify Customer when they place an Order
@receiver(post_save, sender=Order)
def notify_customer_on_order(sender, instance, created, **kwargs):
    if created and instance.user:
        Notification.objects.create(
            recipient=instance.user,
            message=f"Order #{instance.id} placed successfully! We are processing it.",
            order=instance
        )

# 2. Notify Seller when their specific Product is sold
@receiver(post_save, sender=OrderItem)
def notify_seller_on_item_sold(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        seller = product.created_by
        
        # Only notify if the product has a seller and the seller is not buying their own item
        if seller and seller != instance.order.user:
            Notification.objects.create(
                recipient=seller,
                message=f"You made a sale! {instance.quantity}x {product.name} was purchased.",
                order=instance.order
            )

