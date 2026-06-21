document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const offlineToggle = document.getElementById('offline-toggle');
    const syncBadge = document.getElementById('sync-badge');
    const htmlElement = document.documentElement;
    const searchInput = document.getElementById('product-search');
    const productGrid = document.getElementById('product-grid');
    const cartItemsContainer = document.getElementById('cart-items');
    const subtotalEl = document.getElementById('subtotal');
    const grandTotalEl = document.getElementById('grand-total');
    const discountInput = document.getElementById('discount');

    let cart = [];
    let db;

    // Initialize IndexedDB
    const request = indexedDB.open('POS_Offline_DB', 1);
    request.onupgradeneeded = (e) => {
        db = e.target.result;
        if (!db.objectStoreNames.contains('sales')) {
            db.createObjectStore('sales', { keyPath: 'id' });
        }
    };
    request.onsuccess = (e) => {
        db = e.target.result;
        console.log('IndexedDB Initialized');
        checkReconciliation();
    };

    // Offline Toggle Logic
    const savedMode = localStorage.getItem('pos_mode') || 'online';
    offlineToggle.checked = savedMode === 'offline';
    updateSyncUI();

    offlineToggle.addEventListener('change', () => {
        const mode = offlineToggle.checked ? 'offline' : 'online';
        localStorage.setItem('pos_mode', mode);
        updateSyncUI();
        if (mode === 'online') checkReconciliation();
    });

    function updateSyncUI() {
        if (offlineToggle.checked) {
            syncBadge.innerText = '🟡 Offline Storage Mode';
            syncBadge.className = 'badge badge-offline';
        } else {
            syncBadge.innerText = '🟢 Cloud Active';
            syncBadge.className = 'badge badge-online';
        }
    }

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

        retailVal.innerText = Math.round(parseFloat(card.dataset.selectedRetail));
        wholesaleVal.innerText = Math.round(parseFloat(card.dataset.selectedWholesale));

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

    // Explicitly trap 'Enter' to prevent premature message channel termination
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            e.stopPropagation();

            // If there is exactly one product visible, add it to cart
            const visibleCards = Array.from(productGrid.querySelectorAll('.product-card')).filter(c => c.style.display !== 'none');
            if (visibleCards.length === 1) {
                addToCart(visibleCards[0]);
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input'));
            }
        }
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
                    <span>@ ${Math.round(item.price)}</span>
                </div>
                <div style="flex: 0.5; text-align: right;">${Math.round(itemTotal)}</div>
            `;
            cartItemsContainer.appendChild(cartItemEl);
        });

        subtotalEl.innerText = Math.round(subtotal);
        updateGrandTotal();
    }

    function updateGrandTotal() {
        const subtotal = parseFloat(subtotalEl.innerText);
        const discount = parseFloat(discountInput.value) || 0;
        grandTotalEl.innerText = Math.round(subtotal - discount);
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

        const saleId = crypto.randomUUID();
        const data = {
            id: saleId,
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

        if (offlineToggle.checked) {
            saveOffline(data);
        } else {
            processOnline(data);
        }
    });

    async function processOnline(data) {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        try {
            const response = await fetch('/process-sale/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(data)
            });

            const res = await response.json();
            if (res.status === 'success') {
                showReceipt(res.receipt_data);
                finalizeSale();
            } else {
                console.error('Backend error:', res.message);
                alert('Server Error: ' + res.message + '. Saving offline instead.');
                saveOffline(data);
            }
        } catch (err) {
            console.error('Network error / Timeout:', err);
            alert('Connection Lost or Slow Network. Saving transaction offline.');
            saveOffline(data);
        } finally {
            searchInput.focus();
        }
    }

    function saveOffline(data) {
        const transaction = db.transaction(['sales'], 'readwrite');
        const store = transaction.objectStore('sales');
        store.add(data);
        transaction.oncomplete = () => {
            alert('Transaction Saved Locally (Offline Mode).');
            finalizeSale();
        };
        transaction.onerror = (e) => {
            console.error('IndexedDB Error:', e);
            alert('Critical Error: Could not save offline.');
        };
    }

    function showReceipt(data) {
        if (!data) return;
        document.getElementById('rcpt-biz-name').innerText = data.business_name;
        document.getElementById('rcpt-branch').innerText = data.branch_name;
        document.getElementById('rcpt-date').innerText = data.date;
        document.getElementById('rcpt-cashier').innerText = data.cashier;
        document.getElementById('rcpt-total').innerText = data.total;
        document.getElementById('rcpt-currency').innerText = data.currency;

        const itemsBody = document.getElementById('rcpt-items');
        itemsBody.innerHTML = '';
        data.items.forEach(item => {
            const tr = document.createElement('tr');
            tr.style.fontSize = '12px';
            tr.innerHTML = `
                <td>${item.name}</td>
                <td>${item.qty}</td>
                <td style="text-align: right;">${item.price}</td>
            `;
            itemsBody.appendChild(tr);
        });

        document.getElementById('receipt-modal').style.display = 'flex';
    }

    function finalizeSale() {
        cart = [];
        discountInput.value = 0;
        renderCart();
        searchInput.focus();
    }

    async function checkReconciliation() {
        if (offlineToggle.checked || !db) return;

        const transaction = db.transaction(['sales'], 'readonly');
        const store = transaction.objectStore('sales');
        const allSales = store.getAll();

        allSales.onsuccess = async () => {
            const sales = allSales.result;
            if (sales.length === 0) return;

            console.log(`Reconciling ${sales.length} offline transactions...`);
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            for (const sale of sales) {
                try {
                    const response = await fetch('/process-sale/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrftoken
                        },
                        body: JSON.stringify(sale)
                    });
                    const res = await response.json();
                    if (res.status === 'success') {
                        // Success, remove from IndexedDB
                        const delTx = db.transaction(['sales'], 'readwrite');
                        delTx.objectStore('sales').delete(sale.id);
                        console.log(`Synced Sale ${sale.id}`);
                    }
                } catch (err) {
                    console.error('Reconciliation failed for sale:', sale.id, err);
                    break; // Stop loop if network is still down
                }
            }
            console.log('Reconciliation complete/paused.');
        };
    }

    // Auto-check reconciliation when window comes back online
    window.addEventListener('online', checkReconciliation);
});
