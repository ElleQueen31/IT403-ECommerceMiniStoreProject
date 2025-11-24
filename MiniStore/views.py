from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.db import transaction
from django.db.models import Count
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from .forms import ProductForm, SellerRegistrationForm, OrderCheckoutForm, ShippingProfileForm

# --- Import Models, Forms, and Decorators ---
from .models import Product, Category, Order, OrderItem, UserProfile, Notification
try:
    from .decorators import admin_required, seller_required
except ImportError:
    def admin_required(function): return function
    def seller_required(function): return function

CART_SESSION_KEY = "cart"

# ---------------------------------------------------------
#                   CART HELPER
# ---------------------------------------------------------
def _get_cart(session):
    cart = session.get(CART_SESSION_KEY)
    if cart is None:
        cart = {}
        session[CART_SESSION_KEY] = cart
    return cart

# ---------------------------------------------------------
#                   PUBLIC VIEWS
# ---------------------------------------------------------
def product_list(request):
    products_qs = Product.objects.filter(available=True).select_related("category")
    categories = Category.objects.all()

    query = request.GET.get("q")
    if query:
        products_qs = products_qs.filter(name__icontains=query)

    paginator = Paginator(products_qs, 8)
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        "categories": categories,
        "category": None,
        "products": page_obj,
        "page_obj": page_obj,
        "query": query,
    }
    return render(request, "MiniStore/product_list.html", context)

def shop(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products_qs = Product.objects.filter(available=True).select_related("category")

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products_qs = products_qs.filter(category=category)

    query = request.GET.get("q")
    if query:
        products_qs = products_qs.filter(name__icontains=query)

    paginator = Paginator(products_qs, 12)
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        "categories": categories,
        "category": category,
        "products": page_obj,
        "page_obj": page_obj,
        "query": query,
    }
    return render(request, "MiniStore/shop.html", context)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    return render(request, "MiniStore/product_detail.html", {"product": product})

# ---------------------------------------------------------
#                   CART & CHECKOUT
# ---------------------------------------------------------

def cart_detail(request):
    cart = _get_cart(request.session)
    product_ids = cart.keys()
    products = Product.objects.filter(id__in=product_ids)

    cart_items = []
    total = 0
    for product in products:
        pid = str(product.id)
        # Safety check if item exists in session but not db
        if pid in cart:
            quantity = cart[pid]["quantity"]
            item_total = product.price * quantity
            total += item_total
            cart_items.append({
                "product": product,
                "quantity": quantity,
                "price": product.price,
                "item_total": item_total,
            })

    context = {
        "items": cart_items, 
        "cart_items": cart_items, 
        "total": total,
    }
    return render(request, "MiniStore/cart.html", context)

@login_required
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    cart = _get_cart(request.session)
    
    try:
        quantity = int(request.POST.get("quantity", 1))
    except ValueError:
        quantity = 1

    pid = str(product.id)

    if pid in cart:
        cart[pid]["quantity"] += quantity
    else:
        cart[pid] = {"quantity": quantity}

    request.session.modified = True
    total_items = len(cart)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_count': total_items})
    
    return redirect("cart_detail")

@login_required
@require_POST
def cart_update(request, product_id):
    cart = _get_cart(request.session)
    pid = str(product_id)
    
    if pid in cart:
        new_qty = request.POST.get('quantity')
        action = request.POST.get('action')
        
        if new_qty:
            try:
                cart[pid]['quantity'] = int(new_qty)
            except ValueError:
                pass 
        elif action == 'increase':
            cart[pid]['quantity'] += 1
        elif action == 'decrease':
            cart[pid]['quantity'] -= 1
            
        if cart[pid]['quantity'] < 1:
            cart[pid]['quantity'] = 1 
        
        request.session.modified = True
        
        # Recalculate this item
        product = get_object_or_404(Product, id=product_id)
        new_item_total = product.price * cart[pid]['quantity']
        
        # Recalculate global cart total (Note: JS on frontend will update the visual "Selected Total")
        cart_total = 0
        total_quantity = 0
        for key, item_data in cart.items():
            try:
                p = Product.objects.get(id=key)
                cart_total += p.price * item_data['quantity']
                total_quantity += item_data['quantity']
            except Product.DoesNotExist:
                continue

        return JsonResponse({
            'success': True,
            'quantity': cart[pid]['quantity'],
            'item_total': new_item_total,
            'cart_total': cart_total,
            'cart_count': total_quantity
        })
        
    return JsonResponse({'success': False}, status=400)

@login_required
@require_POST
def cart_remove(request, product_id):
    cart = _get_cart(request.session)
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
        request.session.modified = True
        
    total_items = len(cart) 
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
         return JsonResponse({'success': True, 'cart_count': total_items})

    return redirect("cart_detail")

# --- NEW: PROCESS SELECTED ITEMS ---
@login_required
@require_POST
def proceed_to_checkout(request):
    """Stores selected item IDs in session and redirects to checkout."""
    selected_ids = request.POST.getlist('selected_items')
    
    if not selected_ids:
        return redirect('cart_detail')

    # Save selection to session
    request.session['checkout_selected_ids'] = selected_ids
    return redirect('checkout')

@login_required
def checkout(request):
    cart = _get_cart(request.session)
    
    # 1. Get selected IDs (Support for partial checkout)
    selected_ids = request.session.get('checkout_selected_ids', list(cart.keys()))
    
    # 2. Filter: Ensure items actually exist in cart
    valid_selected_ids = [pid for pid in selected_ids if pid in cart]

    if not valid_selected_ids:
        messages.warning(request, "No items selected for checkout.")
        return redirect("cart_detail")

    # 3. Fetch products securely
    products_in_checkout = Product.objects.filter(id__in=valid_selected_ids)

    cart_items = []
    total = 0
    
    for product in products_in_checkout:
        pid = str(product.id)
        if pid in cart:
            quantity = cart[pid]["quantity"]
            item_total = product.price * quantity
            total += item_total
            
            cart_items.append({
                'product': product, 
                'quantity': quantity,
                'item_total': item_total
            })

    if request.method == "POST":
        form = OrderCheckoutForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # A. Create Order
                    order = form.save(commit=False)
                    order.user = request.user
                    order.paid = True  # Assuming COD implies confirmed order
                    order.save()
                    
                    # B. Create Order Items & Remove from Cart
                    for item in cart_items: 
                        OrderItem.objects.create(
                            order=order,
                            product=item['product'],
                            price=item['product'].price,
                            quantity=item['quantity'],
                        )

                        # --- REMOVAL LOGIC ---
                        pid = str(item['product'].id)
                        if pid in cart:
                            del cart[pid] # Remove ONLY checkout items from dict
                    
                    # --- CRITICAL FIX: FORCE SESSION UPDATE ---
                    # Ito ang mag-a-update ng NOTIF BADGE at magbubura sa CART
                    request.session['cart'] = cart 
                    
                    # Clear selection cache
                    if 'checkout_selected_ids' in request.session:
                        del request.session['checkout_selected_ids']

                    # Mark session as modified
                    request.session.modified = True
                    
                return redirect("order_success", order_id=order.id)
            except Exception as e:
                print(f"Checkout Error: {e}") 
                messages.error(request, "An error occurred while placing the order.")
                return redirect("cart_detail")
    else:
        # Pre-fill form from UserProfile
        # Ito yung hinahanap mo na "Acc details ng Acc Owner"
        initial_data = {
            'first_name': getattr(request.user.profile, 'first_name', request.user.first_name),
            'last_name': getattr(request.user.profile, 'last_name', request.user.last_name),
            'email': request.user.email,
            'address': getattr(request.user.profile, 'address', ''),
            'postal_code': getattr(request.user.profile, 'postal_code', ''),
            'city': getattr(request.user.profile, 'city', ''),
        }
        form = OrderCheckoutForm(initial=initial_data)
        
    context = {'form': form, 'cart_items': cart_items, 'total': total}
    # Render the new confirmation template
    return render(request, "MiniStore/checkout_confirm.html", context)

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "MiniStore/order_success.html", {"order": order})

# ---------------------------------------------------------
#                   AUTH & DASHBOARDS
# ---------------------------------------------------------
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user, role='CUSTOMER')
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

def seller_signup(request):
    if request.method == "POST":
        form = SellerRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                UserProfile.objects.create(user=user, role="SELLER")
            login(request, user)
            # Redirect to profile instead of dashboard
            return redirect("profile")
    else: 
        form = SellerRegistrationForm() 
    return render(request, "registration/seller_signup.html", {"form": form})

@login_required(login_url='login')
def profile(request):
    user = request.user
    
    # Ensure profile exists
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user, role='CUSTOMER')

    if request.method == 'POST':
        action = request.POST.get('action')

        # --- A. UPDATE PROFILE INFO & EMAIL ---
        if action == 'update_profile':
            form = ShippingProfileForm(request.POST, instance=profile)
            if form.is_valid(): 
                form.save() 
                new_email = request.POST.get('email')
                if new_email and new_email != user.email:
                    if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                        messages.error(request, "Email address is already in use by another account.")
                    else:
                        user.email = new_email
                        user.save()
                        messages.success(request, "Profile and Email updated successfully.")
                else:
                    messages.success(request, "Profile details updated.")
                return redirect('profile')

        # --- B. UPDATE PASSWORD ---
        elif action == 'change_password':
            current_pass = request.POST.get('current_password')
            new_pass = request.POST.get('new_password')
            confirm_pass = request.POST.get('confirm_password')

            if not user.check_password(current_pass):
                messages.error(request, "Incorrect current password.")
            elif new_pass != confirm_pass:
                messages.error(request, "New passwords do not match.")
            elif len(new_pass) < 6: 
                messages.error(request, "Password must be at least 6 characters long.")
            else:
                user.set_password(new_pass)
                user.save()
                update_session_auth_hash(request, user) 
                messages.success(request, "Password updated successfully!")
            
            return redirect('profile')

    else:
        form = ShippingProfileForm(instance=profile)

    # --- Load Data for Template ---
    my_orders = Order.objects.filter(user=user).order_by('-created')
    seller_products = []
    seller_orders = []
    seller_stats = {'products': 0, 'orders': 0, 'revenue': 0}
    
    if profile.role == 'SELLER':
        seller_products = Product.objects.filter(created_by=user).order_by('-created')
        seller_orders = Order.objects.filter(items__product__in=seller_products).distinct().order_by("-created")

        seller_stats['products'] = seller_products.count()
        seller_stats['orders'] = seller_orders.count()
        revenue = 0
        for order in seller_orders:
            for item in order.items.all():
                if item.product.created_by == user:
                    revenue += item.get_cost()
        seller_stats['revenue'] = revenue

    context = {
        'form': form,
        'profile': profile,
        'my_orders': my_orders,
        'seller_products': seller_products,
        'seller_orders': seller_orders,
        'seller_stats': seller_stats,
        'is_admin': profile.role == 'ADMIN',
    }
    return render(request, 'MiniStore/profile.html', context)


# 1. STATUS A USER 

@login_required
@admin_required
def approve_seller(request, user_id):
    user_to_approve = get_object_or_404(User, pk=user_id)
    profile = user_to_approve.profile
    
    # Update Role and Status
    profile.role = 'SELLER'
    profile.seller_status = 'APPROVED'
    profile.save()
    
    # Notify the User
    Notification.objects.create(
        recipient=user_to_approve,
        message="Congratulations! Your Seller Application has been APPROVED. You can now access your Shop Dashboard.",
    )
    
    messages.success(request, f"Approved {user_to_approve.username} as a Seller.")
    return redirect('admin_dashboard')

@login_required
@admin_required
def deny_seller(request, user_id):
    user_to_deny = get_object_or_404(User, pk=user_id)
    profile = user_to_deny.profile
    
    # Reset to Customer defaults
    profile.role = 'CUSTOMER'
    profile.seller_status = 'NONE'
    profile.save()
    
    # Notify the User
    Notification.objects.create(
        recipient=user_to_deny,
        message="Your Seller Application was not approved at this time. You may apply again later.",
    )
    
    messages.warning(request, f"Denied application for {user_to_deny.username}.")
    return redirect('admin_dashboard')

# ADMIN APPROVE CANCELLATION 
@login_required
@admin_required
def approve_cancellation(request, user_id):
    user_to_demote = get_object_or_404(User, pk=user_id)
    profile = user_to_demote.profile
    
    # Revert to Customer
    profile.role = 'CUSTOMER'
    profile.seller_status = 'NONE'
    profile.save()
    
    Notification.objects.create(
        recipient=user_to_demote,
        message="Your request to stop selling has been approved. Your account is now a Customer account.",
    )
    
    messages.success(request, f"Seller {user_to_demote.username} has been reverted to Customer.")
    return redirect('admin_dashboard')

# SELLER ACTION

@login_required
def become_seller(request):
    profile = request.user.profile
    
    # Check kung 'NONE' pa lang ang status
    if profile.seller_status == 'NONE':
        profile.seller_status = 'PENDING'
        profile.save()
        
        messages.info(request, "Application submitted! Please wait for approval.")
        
        # 2. Notify Admin (Send notif to Superuser)
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"New Seller Application: {request.user.username} wants to join.",
            )
    
    return redirect('profile')

@login_required
def cancel_seller(request):
    profile = request.user.profile
    
    if profile.role == 'SELLER':
        profile.seller_status = 'CANCELLATION_REQUESTED'
        profile.save()
        
        messages.info(request, "Request to stop selling sent to Admin. Please wait for approval.")
        
        # Notify Admin
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                message=f"Cancellation Request: Seller {request.user.username} wants to stop selling.",
            )
            
    return redirect('profile')

# 4. UPDATE: ADMIN DASHBOARD 
@login_required
@admin_required
def admin_dashboard(request):
    # 1. Stats (Binalik ko lahat)
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    total_sellers = UserProfile.objects.filter(role='SELLER').count()
    total_customers = UserProfile.objects.filter(role='CUSTOMER').count()

    # 2. Get Users
    all_users_qs = User.objects.select_related('profile').annotate(
        total_order_count=Count('orders')
    ).exclude(is_superuser=True)

    # 3. Priority Sorting
    def sort_priority(u):
        status = u.profile.seller_status
        if status == 'CANCELLATION_REQUESTED': return 0
        if status == 'PENDING': return 1
        if u.profile.role == 'SELLER': return 2
        return 3

    all_users = sorted(all_users_qs, key=sort_priority)

    context = {
        'total_products': total_products, 
        'total_orders': total_orders,
        'total_sellers': total_sellers,
        'total_customers': total_customers,
        'all_users': all_users,
    }
    return render(request, "MiniStore/admin_dashboard.html", context)

@login_required
@admin_required
def revoke_seller(request, user_id):
    user_to_revoke = get_object_or_404(User, pk=user_id)
    profile = user_to_revoke.profile
    
    if profile.role == 'SELLER':
        profile.role = 'CUSTOMER'
        profile.seller_status = 'NONE'
        profile.save()
        
        Notification.objects.create(
            recipient=user_to_revoke,
            message="Your Seller privileges have been revoked by the Admin.",
        )
        messages.warning(request, f"Revoked seller access for {user_to_revoke.username}.")
    
    return redirect('admin_dashboard')

def seller_signup(request):
    if request.method == "POST":
        form = SellerRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                UserProfile.objects.create(user=user, role="SELLER")
            login(request, user)
            return redirect("seller_dashboard")
    else: form = SellerRegistrationForm() 
    return render(request, "registration/seller_signup.html", {"form": form})

@login_required
def profile_settings(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ShippingProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile_settings') 
    else: form = ShippingProfileForm(instance=profile)
    return render(request, 'MiniStore/profile_settings.html', {'form': form, 'profile': profile})


@login_required
@seller_required
def seller_dashboard(request):
    products = Product.objects.filter(created_by=request.user)
    orders = Order.objects.filter(items__product__in=products).distinct().order_by("-created")
    return render(request, "MiniStore/seller_dashboard.html", {
        "products": products,
        "orders": orders
    })

@login_required
@seller_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            if not product.slug: product.slug = slugify(product.name)
            product.created_by = request.user 
            product.save()
            return redirect('seller_dashboard')
    else: form = ProductForm()
    return render(request, 'MiniStore/product_form.html', {'form': form})

@login_required
@seller_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk, created_by=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('seller_dashboard')
    else: form = ProductForm(instance=product)
    return render(request, 'MiniStore/product_form.html', {'form': form})

@login_required
@seller_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, created_by=request.user)
    if request.method == "POST":
        product.delete()
        return redirect('seller_dashboard')
    return render(request, 'MiniStore/product_confirm_delete.html', {'product': product})

def about(request): return render(request, "MiniStore/about.html")
def contact(request): return render(request, "MiniStore/contact.html")
@login_required
def notification_list(request):
    # Get all notifications for the user
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Mark all unread notifications as read when they visit the page
    unread_notifs = notifications.filter(is_read=False)
    if unread_notifs.exists():
        unread_notifs.update(is_read=True)

    return render(request, "MiniStore/notification_list.html", {"notifications": notifications})

