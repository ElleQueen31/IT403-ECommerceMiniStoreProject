from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

handler403 = 'MiniStore.views.custom_404'

urlpatterns = [
    # HOME PAGE
    path("", views.product_list, name="home"),
    
    # AUTH
    path("login/", auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path("logout/", auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path("signup/", views.signup, name="signup"),
    path("seller/signup/", views.seller_signup, name="seller_signup"), 
    
    # UNIFIED PROFILE
    path("profile/", views.profile, name="profile"),
    # Note: I removed the duplicate 'become-seller' line that was here

    # SELLER APPLICATION PATHS
    path("profile/become-seller/", views.become_seller, name="become_seller"),
    path("profile/cancel-seller/", views.cancel_seller, name="cancel_seller"),

    # ADMIN / MANAGER DASHBOARD
    path("manager/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("manager/approve-seller/<int:user_id>/", views.approve_seller, name="approve_seller"),
    path("manager/deny-seller/<int:user_id>/", views.deny_seller, name="deny_seller"),
    path("manager/approve-cancellation/<int:user_id>/", views.approve_cancellation, name="approve_cancellation"),

    # REVOKING
    path("manager/revoke-seller/<int:user_id>/", views.revoke_seller, name="revoke_seller"),

    # SELLER DASHBOARD
    path("seller/dashboard/", views.seller_dashboard, name="seller_dashboard"),

    # SELLER ACTIONS
    path("seller/product/new/", views.product_create, name="product_create"),
    path("seller/product/<int:pk>/edit/", views.product_update, name="product_update"),
    path("seller/product/<int:pk>/delete/", views.product_delete, name="product_delete"),

    # SHOP
    path("shop/", views.shop, name="shop"),
    path("shop/category/<slug:category_slug>/", views.shop, name="product_list_by_category"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),

    # CART & CHECKOUT
    path("cart/", views.cart_detail, name="cart_detail"),
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"),
    path("cart/update/<int:product_id>/", views.cart_update, name="cart_update"),
    
    # ✅ CHECKBOX CHECKOUT
    path("cart/proceed/", views.proceed_to_checkout, name="proceed_to_checkout"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/<int:order_id>/success/", views.order_success, name="order_success"),

    # STATIC
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("notifications/", views.notification_list, name="notifications"),
]