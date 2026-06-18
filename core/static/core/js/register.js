document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;
    const searchInput = document.getElementById('product-search');
    const productGrid = document.getElementById('product-grid');
    const cartItemsContainer = document.getElementById('cart-items');
    const subtotalEl = document.getElementById('subtotal');
    const grandTotalEl = document.getElementById('grand-total');
    const discountInput = document.getElementById('discount');

    let cart = [];

    // Initialize product cards with first unit prices
    document.querySelectorAll('.product-card').forEach(card => {
        const firstUnit = card.querySelector('.unit-pill');
        if (firstUnit) {
            selectUnit(card, firstUnit);
        }
        card.dataset.mode = 'retail';
    });

    function selectUnit(card, unitPill) {
        card.querySelectorAll('.unit-pill').forEach(p => p.classList.remove('active'));
        unitPill.classList.add('active');
        card.dataset.selectedUnitId = unitPill.dataset.unitId;
        card.dataset.selectedUnitName = unitPill.dataset.unitName;
        card.dataset.selectedRetail = unitPill.dataset.retailPrice;
        card.dataset.selectedWholesale = unitPill.dataset.wholesalePrice;
        updatePriceDisplay(card);
    }

    function updatePriceDisplay(card) {
        const mode = card.dataset.mode;
        const retailVal = card.querySelector('.retail-val');
        const wholesaleVal = card.querySelector('.wholesale-val');
        const retailPill = card.querySelector('.pill-retail');
        const wholesalePill = card.querySelector('.pill-wholesale');

        retailVal.innerText = card.dataset.selectedRetail;
        wholesaleVal.innerText = card.dataset.selectedWholesale;

        if (mode === 'retail') {
            retailPill.style.opacity = '1';
            wholesalePill.style.opacity = '0.5';
        } else {
            retailPill.style.opacity = '0.5';
            wholesalePill.style.opacity = '1';
        }
    }

    // Theme Toggle
    themeToggle.addEventListener('click', () => {
        const currentTheme = htmlElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        htmlElement.setAttribute('data-theme', newTheme);
    });

    // Product Search
    searchInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const cards = productGrid.querySelectorAll('.product-card');
        cards.forEach(card => {
            const name = card.dataset.name.toLowerCase();
            const barcode = card.dataset.barcode.toLowerCase();
            card.style.display = (name.includes(term) || barcode.includes(term)) ? 'flex' : 'none';
        });
    });

    // Handle Clicks on Product Grid
    productGrid.addEventListener('click', (e) => {
        const unitPill = e.target.closest('.unit-pill');
        const retailPill = e.target.closest('.pill-retail');
        const wholesalePill = e.target.closest('.pill-wholesale');
        const card = e.target.closest('.product-card');

        if (unitPill) {
            e.stopPropagation();
            selectUnit(card, unitPill);
            return;
        }

        if (retailPill) {
            e.stopPropagation();
            card.dataset.mode = 'retail';
            updatePriceDisplay(card);
            return;
        }

        if (wholesalePill) {
            e.stopPropagation();
            card.dataset.mode = 'wholesale';
            updatePriceDisplay(card);
            return;
        }

        if (card) {
            addToCart(card);
        }
    });

    function addToCart(card) {
        const unitId = card.dataset.selectedUnitId;
        const mode = card.dataset.mode;
        const price = mode === 'retail' ? parseFloat(card.dataset.selectedRetail) : parseFloat(card.dataset.selectedWholesale);

        // We allow multiple items of same unit but different mode if needed,
        // but typically one unit id is enough. Let's include mode in the unique key.
        const cartKey = `${unitId}-${mode}`;
        const existingItem = cart.find(item => item.cartKey === cartKey);

        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            cart.push({
                cartKey: cartKey,
                unitId: unitId,
                productId: card.dataset.id,
                name: card.dataset.name,
                unitName: card.dataset.selectedUnitName,
                mode: mode,
                price: price,
                quantity: 1
            });
        }
        renderCart();
    }

    function renderCart() {
        cartItemsContainer.innerHTML = '';
        let subtotal = 0;

        cart.forEach((item, index) => {
            const itemTotal = item.price * item.quantity;
            subtotal += itemTotal;

            const cartItemEl = document.createElement('div');
            cartItemEl.className = 'cart-item';

            const product = productsData[item.productId];
            let unitOptions = product.units.map(u =>
                `<option value="${u.id}" ${u.id === item.unitId ? 'selected' : ''}>${u.name}</option>`
            ).join('');

            cartItemEl.innerHTML = `
                <div style="flex: 2">
                    <strong>${item.name}</strong> (${item.mode})<br>
                    <select class="cart-unit-select" data-index="${index}">
                        ${unitOptions}
                    </select>
                </div>
                <div style="flex: 1; display: flex; align-items: center; gap: 5px;">
                    <input type="number" value="${item.quantity}" min="1" style="width: 45px;" data-index="${index}" class="qty-input">
                    <span>@ ${item.price.toFixed(2)}</span>
                </div>
                <div style="flex: 0.5; text-align: right;">${itemTotal.toFixed(2)}</div>
            `;
            cartItemsContainer.appendChild(cartItemEl);
        });

        subtotalEl.innerText = subtotal.toFixed(2);
        updateGrandTotal();
    }

    function updateGrandTotal() {
        const subtotal = parseFloat(subtotalEl.innerText);
        const discount = parseFloat(discountInput.value) || 0;
        grandTotalEl.innerText = (subtotal - discount).toFixed(2);
    }

    cartItemsContainer.addEventListener('input', (e) => {
        const index = e.target.dataset.index;
        if (e.target.classList.contains('qty-input')) {
            cart[index].quantity = parseInt(e.target.value) || 1;
            renderCart();
        }
        if (e.target.classList.contains('cart-unit-select')) {
            const newUnitId = e.target.value;
            const product = productsData[cart[index].productId];
            const newUnit = product.units.find(u => u.id === newUnitId);
            const mode = cart[index].mode;
            cart[index].unitId = newUnitId;
            cart[index].unitName = newUnit.name;
            cart[index].price = mode === 'retail' ? newUnit.retail : newUnit.wholesale;
            cart[index].cartKey = `${newUnitId}-${mode}`;
            renderCart();
        }
    });

    discountInput.addEventListener('input', updateGrandTotal);

    document.getElementById('save-print').addEventListener('click', () => {
        if (cart.length === 0) {
            alert('Cart is empty!');
            return;
        }

        const data = {
            cart: cart.map(item => ({
                unit_id: item.unitId,
                quantity: item.quantity,
                price: item.price
            })),
            payment_mode: document.getElementById('payment-mode').value,
            status: document.getElementById('transaction-status').value,
            discount: parseFloat(discountInput.value) || 0,
            total: parseFloat(grandTotalEl.innerText)
        };

        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        fetch('/process-sale/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(res => {
            if (res.status === 'success') {
                alert('Transaction Saved! Sale ID: ' + res.sale_id);
                cart = [];
                discountInput.value = 0;
                renderCart();
            } else {
                alert('Error saving transaction: ' + res.message);
            }
        })
        .catch(err => {
            console.error(err);
            alert('Error connecting to server.');
        });
    });
});
