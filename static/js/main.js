// ── CART (Server-side persistent) ────────────────────────────────────────────
let cart = [];
let cartLoaded = false;

async function loadCart() {
  if (!window.__userLoggedIn) { cart = []; updateCartCount(); return; }
  try {
    const res = await fetch('/api/user/cart');
    if (res.ok) {
      cart = await res.json();
      cartLoaded = true;
      updateCartCount();
      if (window.renderCart) renderCart();
    }
  } catch(e) { console.error('Cart load failed', e); }
}

async function saveCartToServer() {
  if (!window.__userLoggedIn) return;
  try {
    await fetch('/api/user/cart', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ items: cart.map(i => ({ _id: i._id, qty: i.qty })) })
    });
  } catch(e) { console.error('Cart save failed', e); }
}

function updateCartCount() {
  const count = cart.filter(i => i.available !== false).reduce((s, i) => s + i.qty, 0);
  document.querySelectorAll('#cartCount').forEach(el => el.textContent = count);
}

async function addToCart(product) {
  if (!window.__userLoggedIn) {
    sessionStorage.setItem('hcn_pending_cart', JSON.stringify(product));
    showToast('Please login to add items to cart', 'error');
    setTimeout(() => { window.location.href = '/login?next=/products'; }, 900);
    return;
  }
  const existing = cart.find(i => i._id === (product._id?.$oid || product._id));
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({
      _id: product._id?.$oid || product._id,
      name: product.name,
      price: product.price,
      image: product.image || '',
      category: product.category || '',
      qty: 1,
      available: true
    });
  }
  updateCartCount();
  showToast(`${product.name} added to cart!`, 'success');
  await saveCartToServer();
}

async function removeFromCart(id) {
  cart = cart.filter(i => i._id !== id);
  updateCartCount();
  await saveCartToServer();
  if (window.renderCart) renderCart();
}

async function updateQty(id, qty) {
  const item = cart.find(i => i._id === id);
  if (item) {
    item.qty = Math.max(1, qty);
    updateCartCount();
    await saveCartToServer();
    if (window.renderCart) renderCart();
  }
}

function getCartTotal() {
  return cart.filter(i => i.available !== false).reduce((sum, i) => sum + i.price * i.qty, 0);
}

// ── TOAST ─────────────────────────────────────────────────────────────────────
function showToast(msg, type = '') {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.className = 'toast show ' + type;
  setTimeout(() => toast.className = 'toast', 2500);
}

// ── SEARCH ────────────────────────────────────────────────────────────────────
let allProductsCache = null;

async function fetchAllProducts() {
  if (allProductsCache) return allProductsCache;
  try {
    const res = await fetch('/api/products');
    allProductsCache = await res.json();
  } catch(e) { allProductsCache = []; }
  return allProductsCache;
}

function toggleSearch() {
  const bar = document.getElementById('searchBar');
  if (bar) {
    bar.classList.toggle('open');
    if (bar.classList.contains('open')) {
      const inp = document.getElementById('searchInput');
      if (inp) inp.focus();
      fetchAllProducts();
    } else {
      closeSearchDropdown();
    }
  }
}

function handleSearchInput(e) {
  if (e.key === 'Enter') doSearch();
  else if (e.key === 'Escape') toggleSearch();
}

async function liveSearch(query) {
  const dropdown = document.getElementById('searchDropdown');
  if (!dropdown) return;
  const q = query.trim().toLowerCase();
  if (!q) { closeSearchDropdown(); return; }

  const products = await fetchAllProducts();
  const matched = products.filter(p => {
    const name = (p.name || '').toLowerCase();
    return q.split(/\s+/).some(word => word && name.includes(word));
  });

  if (!matched.length) {
    dropdown.innerHTML = `<div class="search-no-result"><i class="fas fa-search"></i>No products found for "<b>${query}</b>"</div>`;
    dropdown.classList.add('show');
    return;
  }

  dropdown.innerHTML = matched.slice(0, 8).map(p => `
    <div class="search-result-item" onclick="openProductModal('${p._id.$oid || p._id}');closeSearchDropdown();">
      <img class="search-result-img" src="${p.image || '/static/images/logo.png'}" alt="${p.name}" onerror="this.src='/static/images/logo.png'">
      <div class="search-result-info">
        <div class="search-result-name">${p.name}</div>
        <div class="search-result-cat">${p.category || ''}</div>
      </div>
      <div class="search-result-price">₹${p.price ? p.price.toFixed(2) : '-'}</div>
    </div>
  `).join('');
  dropdown.classList.add('show');
}

function closeSearchDropdown() {
  const dropdown = document.getElementById('searchDropdown');
  if (dropdown) dropdown.classList.remove('show');
}

function searchProducts(e) {
  if (e.key === 'Enter') doSearch();
}

function doSearch() {
  const q = document.getElementById('searchInput').value.trim();
  if (q) window.location.href = `/products?search=${encodeURIComponent(q)}`;
}

// ── MOBILE MENU ───────────────────────────────────────────────────────────────
function openMobileMenu() {
  const links = document.querySelector('.nav-links');
  const overlay = document.getElementById('mobileNavOverlay');
  if (!links) return;
  if (!links.querySelector('.mobile-nav-header')) {
    const header = document.createElement('div');
    header.className = 'mobile-nav-header';
    header.innerHTML = `<img src="/static/images/logo.png" style="height:32px;"> <button class="mobile-close-btn" onclick="closeMobileMenu()"><i class="fas fa-times"></i></button>`;
    links.insertBefore(header, links.firstChild);
  }
  links.classList.add('mobile-open');
  if (overlay) overlay.classList.add('open');
  document.body.style.overflow = 'hidden';
  links.querySelectorAll('.has-dropdown > a').forEach(a => {
    a.onclick = function(e) {
      if (window.innerWidth <= 768) {
        e.preventDefault();
        a.parentElement.classList.toggle('expanded');
      }
    };
  });
}

function closeMobileMenu() {
  const links = document.querySelector('.nav-links');
  const overlay = document.getElementById('mobileNavOverlay');
  if (links) links.classList.remove('mobile-open');
  if (overlay) overlay.classList.remove('open');
  document.body.style.overflow = '';
}

function toggleMobileMenu() { openMobileMenu(); }

// ── PRODUCT MODAL ─────────────────────────────────────────────────────────────
let currentProduct = null;
let modalQty = 1;

async function openProductModal(productId) {
  try {
    const res = await fetch(`/api/products/${productId}`);
    if (!res.ok) { showToast('Product not available', 'error'); return; }
    const p = await res.json();
    if (p.error) { showToast('Product not available', 'error'); return; }
    currentProduct = p;
    modalQty = 1;

    const modal = document.getElementById('productModal');
    if (!modal) return;

    modal.querySelector('#modal-img').src = p.image || '/static/images/placeholder.png';
    modal.querySelector('#modal-img').alt = p.name;
    modal.querySelector('#modal-name').textContent = p.name;
    modal.querySelector('#modal-price').textContent = '₹' + p.price.toFixed(2);
    modal.querySelector('#modal-desc').textContent = p.description || '';
    modal.querySelector('#modal-weight').textContent = p.weight || '-';
    modal.querySelector('#modal-sku').textContent = p.sku || '-';
    modal.querySelector('#modal-stock').textContent = p.stock > 0 ? 'In Stock' : 'Out of Stock';
    modal.querySelector('#modal-qty').textContent = modalQty;

    const featuresEl = modal.querySelector('#modal-features');
    if (featuresEl) {
      featuresEl.innerHTML = '';
      (p.features || []).forEach(f => { if (f.trim()) featuresEl.innerHTML += `<li>${f}</li>`; });
    }

    const mrpEl = modal.querySelector('#modal-mrp');
    if (mrpEl && p.mrp && p.mrp > p.price) {
      mrpEl.style.display = '';
      mrpEl.textContent = '₹' + p.mrp.toFixed(2);
      const discPct = Math.round((1 - p.price / p.mrp) * 100);
      const discEl = modal.querySelector('#modal-discount');
      if (discEl) { discEl.textContent = discPct + '% off'; discEl.style.display = ''; }
    } else if (mrpEl) {
      mrpEl.style.display = 'none';
      const discEl = modal.querySelector('#modal-discount');
      if (discEl) discEl.style.display = 'none';
    }

    modal.classList.add('open');
  } catch(e) { console.error(e); }
}

function closeProductModal() {
  const modal = document.getElementById('productModal');
  if (modal) modal.classList.remove('open');
}

function changeModalQty(delta) {
  modalQty = Math.max(1, modalQty + delta);
  const el = document.getElementById('modal-qty');
  if (el) el.textContent = modalQty;
}

function addModalToCart() {
  if (!currentProduct) return;
  for (let i = 0; i < modalQty; i++) addToCart(currentProduct);
  closeProductModal();
}

function buyNow() {
  if (!currentProduct) return;
  if (!window.__userLoggedIn) {
    sessionStorage.setItem('hcn_pending_cart', JSON.stringify(currentProduct));
    showToast('Please login to continue', 'error');
    setTimeout(() => { window.location.href = '/login?next=/cart'; }, 900);
    return;
  }
  addToCart(currentProduct);
  window.location.href = '/cart';
}

// ── INIT ──────────────────────────────────────────────────────────────────────
loadCart();

document.addEventListener('click', function(e) {
  const bar = document.getElementById('searchBar');
  if (bar && !bar.contains(e.target)) closeSearchDropdown();
});
