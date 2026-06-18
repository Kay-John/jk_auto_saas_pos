import json
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from decimal import Decimal
from .models import Product, ProductUnit, Branch, BranchStock, Supplier, StockTransaction, Sale, SaleItem, Tenant, UserProfile
from .forms import TenantSignupForm

def signup_view(request):
    if request.user.is_authenticated:
        return redirect_user_by_role(request.user)

    if request.method == 'POST':
        form = TenantSignupForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Create Tenant
                    tenant = Tenant.objects.create(
                        name=form.cleaned_data['business_name'],
                        currency=form.cleaned_data['currency'],
                        subscription_status='trial',
                        trial_ends_at=timezone.now() + timedelta(days=14)
                    )

                    # 2. Create Default Branch
                    branch = Branch.objects.create(
                        tenant=tenant,
                        name=f"{tenant.name} Head Office"
                    )

                    # 3. Create Admin User
                    # Splitting full name into first/last for AbstractUser compatibility
                    full_name = form.cleaned_data['admin_full_name']
                    name_parts = full_name.split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ""

                    user = UserProfile.objects.create_user(
                        username=form.cleaned_data['email'], # Using email as username
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password'],
                        first_name=first_name,
                        last_name=last_name,
                        role='TENANT_ADMIN',
                        tenant=tenant,
                        branch=branch
                    )

                    login(request, user)
                    messages.success(request, "Welcome to your SaaS POS! Your 14-day free trial has begun. Let's start by adding your first product or supplier.")
                    return redirect('inventory_dashboard')
            except Exception as e:
                form.add_error(None, f"An error occurred during provisioning: {str(e)}")
    else:
        form = TenantSignupForm()

    return render(request, 'core/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect_user_by_role(request.user)

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user is not None:
            login(request, user)
            return redirect_user_by_role(user)
        else:
            return render(request, 'core/login.html', {'error': 'Invalid credentials'})

    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def redirect_user_by_role(user):
    if user.role == 'CASHIER':
        return redirect('register_screen')
    else:
        return redirect('inventory_dashboard')

@login_required
@role_required(['TENANT_ADMIN', 'BRANCH_MANAGER', 'CASHIER'])
def register_screen(request):
    user = request.user
    # Sandboxing: Only products belonging to the user's tenant
    products = Product.objects.filter(tenant=user.tenant).prefetch_related('units')

    # Get current branch stock for warnings
    branch_stock_map = {}
    if user.branch:
        stocks = BranchStock.objects.filter(branch=user.branch)
        for s in stocks:
            branch_stock_map[s.product_id] = s.quantity

    return render(request, 'core/register.html', {
        'products': products,
        'branch_stock_map': branch_stock_map
    })

@login_required
@role_required(['TENANT_ADMIN', 'BRANCH_MANAGER'])
def inventory_dashboard(request):
    user = request.user

    # Sandboxing based on roles
    if user.role == 'TENANT_ADMIN':
        branches = Branch.objects.filter(tenant=user.tenant)
        all_products_qs = Product.objects.filter(tenant=user.tenant).prefetch_related('units', 'branch_stocks')
        suppliers = Supplier.objects.filter(tenant=user.tenant)
    else: # BRANCH_MANAGER
        branches = Branch.objects.filter(id=user.branch_id)
        all_products_qs = Product.objects.filter(tenant=user.tenant).prefetch_related('units', 'branch_stocks')
        suppliers = Supplier.objects.filter(tenant=user.tenant)

    # Apply Global Search Filters
    q = request.GET.get('q')
    category = request.GET.get('category')
    if q:
        all_products_qs = all_products_qs.filter(Q(name__icontains=q) | Q(barcode__icontains=q))
    if category:
        all_products_qs = all_products_qs.filter(category__icontains=category)

    # Pagination for Product Catalog
    paginator = Paginator(all_products_qs, 10) # 10 products per page
    page_number = request.GET.get('page')
    products_page = paginator.get_page(page_number)

    # Efficiently fetch all stock data in one query, limited by sandbox
    if user.role == 'TENANT_ADMIN':
        all_stocks = BranchStock.objects.filter(branch__tenant=user.tenant)
    else:
        all_stocks = BranchStock.objects.filter(branch=user.branch)

    stock_map = {} # (product_id, branch_id) -> quantity
    for bs in all_stocks:
        stock_map[(bs.product_id, bs.branch_id)] = bs.quantity

    # Simple stock monitor cross-ref data (only for the current page of products)
    stock_grid = []
    for product in products_page:
        row = {'product': product, 'branch_stock': {}}
        for branch in branches:
            row['branch_stock'][branch.id] = stock_map.get((product.id, branch.id), 0)
        stock_grid.append(row)

    return render(request, 'core/inventory.html', {
        'products': products_page, # This is the paginated object
        'branches': branches,
        'suppliers': suppliers,
        'stock_grid': stock_grid,
        'all_products': all_products_qs # Need full list for some dropdowns if needed, or just use page
    })

@login_required
@role_required(['TENANT_ADMIN', 'BRANCH_MANAGER'])
def stock_intake(request):
    if request.method == 'POST':
        user = request.user
        product_id = request.POST.get('product')
        branch_id = request.POST.get('branch')
        unit_id = request.POST.get('unit')
        supplier_id = request.POST.get('supplier')
        quantity_str = request.POST.get('quantity', '0')
        quantity = Decimal(quantity_str) if quantity_str else Decimal('0')

        # IDOR Protection: Ensure objects belong to the user's tenant
        try:
            product = Product.objects.get(id=product_id, tenant=user.tenant)
            unit = ProductUnit.objects.get(id=unit_id, product=product)
            branch = Branch.objects.get(id=branch_id, tenant=user.tenant)

            # If Branch Manager, only allow intake for their own branch
            if user.role == 'BRANCH_MANAGER' and str(branch.id) != str(user.branch_id):
                 return render(request, 'core/403.html', status=403)

            supplier = None
            if supplier_id and supplier_id != '':
                supplier = Supplier.objects.get(id=supplier_id, tenant=user.tenant)
        except (Product.DoesNotExist, ProductUnit.DoesNotExist, Branch.DoesNotExist, Supplier.DoesNotExist):
            return render(request, 'core/403.html', status=403)

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

@login_required
@transaction.atomic
def process_sale(request):
    if request.method == 'POST':
        try:
            user = request.user
            data = json.loads(request.body)
            sale_id = data.get('id')

            # Check for existing sale to prevent double-syncing
            if sale_id and Sale.objects.filter(id=sale_id).exists():
                 return JsonResponse({'status': 'success', 'sale_id': str(sale_id), 'note': 'Duplicate ignored'})

            cart = data.get('cart', [])
            payment_mode = data.get('payment_mode', 'CASH')
            discount = Decimal(str(data.get('discount', 0)))
            total_amount = Decimal(str(data.get('total', 0)))

            # Secure multi-tenant context from user session
            branch = user.branch
            tenant = user.tenant

            if not branch or not tenant:
                 return JsonResponse({'status': 'error', 'message': 'User not assigned to a branch/tenant'}, status=400)

            sale = Sale.objects.create(
                id=sale_id if sale_id else uuid.uuid4(),
                tenant=tenant,
                branch=branch,
                payment_mode=payment_mode,
                status='PAID',
                discount=discount,
                total_amount=total_amount,
                balance_due=0
            )

            for item in cart:
                # IDOR Protection: Verify ProductUnit belongs to the tenant
                try:
                    product_unit = ProductUnit.objects.get(id=item['unit_id'], product__tenant=tenant)
                except ProductUnit.DoesNotExist:
                    continue # Or abort the whole sale

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
