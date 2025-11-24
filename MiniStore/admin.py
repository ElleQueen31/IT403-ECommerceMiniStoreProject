from django.contrib import admin

from .models import Category, Order, OrderItem, Product, UserProfile


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ["product"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "first_name", "last_name", "paid", "created"]
    list_filter = ["paid", "created", "updated"]
    inlines = [OrderItemInline]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "price", "stock", "available", "created"]
    list_filter = ["available", "created", "updated", "category"]
    list_editable = ["price", "stock", "available"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role"]
    list_filter = ["role"]
