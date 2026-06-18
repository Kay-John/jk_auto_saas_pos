from django.shortcuts import render
from .models import Product, ProductUnit

def register_screen(request):
    products = Product.objects.all().prefetch_related('units')
    return render(request, 'core/register.html', {
        'products': products
    })
