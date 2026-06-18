import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
from .models import Product, ProductUnit, Branch, BranchStock, Supplier, StockTransaction, Sale, SaleItem

def register_screen(request):
    products = Product.objects.all().prefetch_related('units')
    return render(request, 'core/register.html', {
        'products': products
    })

def inventory_dashboard(request):
    products = Product.objects.all().prefetch_related('units', 'branch_stocks')
    branches = Branch.objects.all()
    suppliers = Supplier.objects.all()

    # Efficiently fetch all stock data in one query
    all_stocks = BranchStock.objects.all()
    stock_map = {} # (product_id, branch_id) -> quantity
    for bs in all_stocks:
        stock_map[(bs.product_id, bs.branch_id)] = bs.quantity

    # Simple stock monitor cross-ref data
    stock_grid = []
    for product in products:
        row = {'product': product, 'branch_stock': {}}
        for branch in branches:
            row['branch_stock'][branch.id] = stock_map.get((product.id, branch.id), 0)
        stock_grid.append(row)

    return render(request, 'core/inventory.html', {
        'products': products,
        'branches': branches,
        'suppliers': suppliers,
        'stock_grid': stock_grid
    })

def stock_intake(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        branch_id = request.POST.get('branch')
        unit_id = request.POST.get('unit')
        supplier_id = request.POST.get('supplier')
        quantity_str = request.POST.get('quantity', '0')
        quantity = Decimal(quantity_str) if quantity_str else Decimal('0')

        product = Product.objects.get(id=product_id)
        branch = Branch.objects.get(id=branch_id)
        unit = ProductUnit.objects.get(id=unit_id)
        supplier = Supplier.objects.get(id=supplier_id) if supplier_id and supplier_id != '' else None

        quantity_base = quantity * unit.conversion_factor

        with transaction.atomic():
            # Update BranchStock
            bs, created = BranchStock.objects.get_or_create(branch=branch, product=product)
            bs.quantity += quantity_base
            bs.save()

            # Log Transaction
            StockTransaction.objects.create(
                branch=branch,
                product=product,
                product_unit=unit,
                quantity=quantity,
                quantity_base=quantity_base,
                transaction_type='IN',
                supplier=supplier
            )

        return redirect('inventory_dashboard')
    return redirect('inventory_dashboard')

@transaction.atomic
def process_sale(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cart = data.get('cart', [])
            payment_mode = data.get('payment_mode', 'CASH')
            discount = Decimal(str(data.get('discount', 0)))
            total_amount = Decimal(str(data.get('total', 0)))

            # For this demo, we'll pick the first branch/tenant or use request.user info if available
            # Ideally, this should come from the session or user profile
            branch = Branch.objects.first()
            tenant = branch.tenant if branch else Tenant.objects.first()

            sale = Sale.objects.create(
                tenant=tenant,
                branch=branch,
                payment_mode=payment_mode,
                status='PAID',
                discount=discount,
                total_amount=total_amount,
                balance_due=0
            )

            for item in cart:
                product_unit = ProductUnit.objects.get(id=item['unit_id'])
                quantity = Decimal(str(item['quantity']))

                SaleItem.objects.create(
                    sale=sale,
                    product_unit=product_unit,
                    quantity=quantity,
                    unit_price=Decimal(str(item['price']))
                )

                # Update Stock
                quantity_base = quantity * product_unit.conversion_factor
                bs, created = BranchStock.objects.get_or_create(branch=branch, product=product_unit.product)
                bs.quantity -= quantity_base
                bs.save()

                # Log Out Transaction
                StockTransaction.objects.create(
                    branch=branch,
                    product=product_unit.product,
                    product_unit=product_unit,
                    quantity=quantity,
                    quantity_base=quantity_base,
                    transaction_type='OUT'
                )

            return JsonResponse({'status': 'success', 'sale_id': str(sale.id)})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
