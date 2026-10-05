const API_BASE = '';

const state = {
    currentRoute: 'dashboard',
    items: [],
    matches: [],
    dashboardStats: null,
};

const router = {
    routes: {
        '/': 'dashboard',
        '/report/lost': 'report-lost',
        '/report/found': 'report-found',
        '/browse/lost': 'browse-lost',
        '/browse/found': 'browse-found',
        '/matches': 'matches',
    },

    navigate(path) {
        window.location.hash = '#' + path;
    },

    resolve() {
        const hash = window.location.hash.slice(1) || '/';
        const path = hash.split('?')[0];

        if (this.routes[path]) {
            return this.routes[path];
        }

        const itemMatch = path.match(/^\/item\/(\d+)$/);
        if (itemMatch) {
            return 'item-detail';
        }

        return 'dashboard';
    },
};

function api(endpoint, options = {}) {
    return fetch(API_BASE + endpoint, {
        headers: options.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
        ...options,
    }).then(res => {
        if (!res.ok) {
            return res.json().then(err => { throw new Error(err.detail || 'Request failed'); });
        }
        return res.json();
    });
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

function openModal(content) {
    document.getElementById('modalContent').innerHTML = content;
    document.getElementById('modalOverlay').classList.add('active');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
}

function formatDate(dateStr) {
    if (!dateStr) return 'Unknown';
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch {
        return dateStr;
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getItemImage(item) {
    if (item.image_path) {
        return `<img src="${item.image_path}" alt="${escapeHtml(item.title)}" class="item-card-image">`;
    }
    const icons = { electronics: '📱', clothing: '👕', accessories: '👜', books: '📚', sports: '⚽', other: '📦' };
    const icon = icons[item.category] || '📦';
    return `<div class="item-card-image-placeholder">${icon}</div>`;
}

function renderDashboard() {
    const s = state.dashboardStats || { total_lost: 0, total_found: 0, pending_matches: 0, confirmed_matches: 0, reunited_items: 0 };

    const recentItems = state.items.slice(0, 6);
    const recentMatches = state.matches.slice(0, 3);

    return `
        <div class="page-header">
            <h1>Dashboard</h1>
            <p>AI-powered lost and found matching for campus</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">🔴</div>
                <div class="stat-value">${s.total_lost}</div>
                <div class="stat-label">Lost Items</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🟢</div>
                <div class="stat-value">${s.total_found}</div>
                <div class="stat-label">Found Items</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🔗</div>
                <div class="stat-value">${s.pending_matches}</div>
                <div class="stat-label">Potential Matches</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-value">${s.reunited_items}</div>
                <div class="stat-label">Reunited Items</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
            <div class="card">
                <div class="card-header">Recent Items</div>
                <div class="card-body">
                    ${recentItems.length ? `<div class="items-grid" style="grid-template-columns: 1fr;">${recentItems.map(item => renderItemCard(item)).join('')}</div>` : '<div class="empty-state"><div class="empty-state-icon">📭</div><div class="empty-state-text">No items yet</div></div>'}
                </div>
            </div>
            <div class="card">
                <div class="card-header">Recent Matches</div>
                <div class="card-body">
                    ${recentMatches.length ? recentMatches.map(m => renderMatchCard(m, true)).join('') : '<div class="empty-state"><div class="empty-state-icon">🔗</div><div class="empty-state-text">No matches yet</div></div>'}
                </div>
            </div>
        </div>

        <div class="card" style="margin-top: 24px;">
            <div class="card-header">How It Works</div>
            <div class="card-body">
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; text-align: center;">
                    <div style="padding: 20px;">
                        <div style="font-size: 2.5rem; margin-bottom: 12px;">📤</div>
                        <h3 style="margin-bottom: 8px;">1. Report</h3>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">Upload a photo and describe your lost or found item</p>
                    </div>
                    <div style="padding: 20px;">
                        <div style="font-size: 2.5rem; margin-bottom: 12px;">🤖</div>
                        <h3 style="margin-bottom: 8px;">2. AI Analysis</h3>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">Our AI extracts features and finds potential matches</p>
                    </div>
                    <div style="padding: 20px;">
                        <div style="font-size: 2.5rem; margin-bottom: 12px;">🎉</div>
                        <h3 style="margin-bottom: 8px;">3. Reunite</h3>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">Confirm matches and get your item back</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderItemCard(item) {
    const statusClass = item.type === 'lost' ? 'tag-lost' : 'tag-found';
    const statusText = item.type === 'lost' ? 'Lost' : 'Found';

    return `
        <div class="item-card" onclick="viewItem(${item.id})">
            ${getItemImage(item)}
            <div class="item-card-body">
                <div class="item-card-title">${escapeHtml(item.title)}</div>
                <div class="item-card-meta">
                    <span>📍 ${escapeHtml(item.location)}</span>
                    <span>•</span>
                    <span>${formatDate(item.date_time)}</span>
                </div>
                <div class="item-card-tags">
                    <span class="tag ${statusClass}">${statusText}</span>
                    ${item.category ? `<span class="tag tag-category">${escapeHtml(item.category)}</span>` : ''}
                    ${item.color ? `<span class="tag">${escapeHtml(item.color)}</span>` : ''}
                    ${item.brand ? `<span class="tag">${escapeHtml(item.brand)}</span>` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderReportForm(type) {
    const isLost = type === 'lost';
    const title = isLost ? 'Report Lost Item' : 'Report Found Item';
    const icon = isLost ? '🔴' : '🟢';

    return `
        <div class="page-header">
            <h1>${icon} ${title}</h1>
            <p>Our AI will analyze the image and find potential matches</p>
        </div>

        <div class="card">
            <div class="card-body">
                <form id="reportForm" onsubmit="submitReport(event, '${type}')">
                    <div class="form-group">
                        <label class="form-label">Photo ${isLost ? '(of the lost item)' : '(of the found item)'}</label>
                        <div class="file-upload" id="fileUpload" onclick="document.getElementById('imageInput').click()">
                            <div class="file-upload-icon">📷</div>
                            <div class="file-upload-text">Click or drag to upload an image</div>
                            <input type="file" id="imageInput" accept="image/*" onchange="previewImage(this)">
                        </div>
                        <div id="filePreview"></div>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="title">Item Title <span class="required">*</span></label>
                        <input type="text" id="title" class="form-input" placeholder="e.g., Black iPhone 13 with blue case" required>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="description">Description</label>
                        <textarea id="description" class="form-textarea" placeholder="Any additional details that might help identify this item..."></textarea>
                        <div class="form-hint">The AI will analyze this along with the image</div>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="location">Location <span class="required">*</span></label>
                        <input type="text" id="location" class="form-input" placeholder="e.g., AB2 Library, Student Center" required>
                    </div>

                    <div class="form-group">
                        <label class="form-label" for="date_time">Date & Time <span class="required">*</span></label>
                        <input type="datetime-local" id="date_time" class="form-input" required>
                    </div>

                    <div id="aiAnalysisResult"></div>

                    <div style="display: flex; gap: 12px; margin-top: 24px;">
                        <button type="submit" class="btn btn-primary" id="submitBtn">
                            <span>Submit Report</span>
                        </button>
                        <button type="button" class="btn btn-outline" onclick="router.navigate('/')">Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    `;
}

function renderBrowse(type) {
    const isLost = type === 'lost';
    const title = isLost ? 'Lost Items' : 'Found Items';
    const icon = isLost ? '🔴' : '🟢';

    const items = state.items.filter(i => i.type === type && i.status === 'active');

    return `
        <div class="page-header">
            <h1>${icon} ${title}</h1>
            <p>Browse all ${type} items on campus</p>
        </div>

        <div class="filters">
            <input type="text" class="search-input" id="searchInput" placeholder="Search items..." oninput="filterItems(this.value, '${type}')">
            <select class="filter-select" id="categoryFilter" onchange="filterByCategory(this.value, '${type}')">
                <option value="">All Categories</option>
                <option value="electronics">Electronics</option>
                <option value="clothing">Clothing</option>
                <option value="accessories">Accessories</option>
                <option value="books">Books</option>
                <option value="sports">Sports</option>
                <option value="other">Other</option>
            </select>
        </div>

        <div id="itemsList">
            ${items.length ? `<div class="items-grid">${items.map(item => renderItemCard(item)).join('')}</div>` : '<div class="empty-state"><div class="empty-state-icon">📭</div><div class="empty-state-text">No items found</div></div>'}
        </div>
    `;
}

function renderMatches() {
    const matches = state.matches;

    return `
        <div class="page-header">
            <h1>🔗 Potential Matches</h1>
            <p>AI-discovered matches between lost and found items</p>
        </div>

        <div class="filters">
            <select class="filter-select" id="statusFilter" onchange="filterMatches(this.value)">
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="confirmed">Confirmed</option>
                <option value="rejected">Rejected</option>
            </select>
        </div>

        <div id="matchesList">
            ${matches.length ? matches.map(m => renderMatchCard(m)).join('') : '<div class="empty-state"><div class="empty-state-icon">🔗</div><div class="empty-state-text">No matches found</div></div>'}
        </div>
    `;
}

function renderMatchCard(m, compact = false) {
    const scorePercent = Math.round(m.score * 100);
    const statusClass = m.status === 'confirmed' ? 'badge-confirmed' : m.status === 'rejected' ? 'badge-rejected' : 'badge-pending';
    const statusText = m.status.charAt(0).toUpperCase() + m.status.slice(1);

    const lostItem = m.lost_item || {};
    const foundItem = m.found_item || {};

    if (compact) {
        return `
            <div class="match-card" onclick="viewMatch(${m.id})" style="cursor: pointer;">
                <div class="match-header">
                    <div class="match-score">
                        <span class="match-score-value">${scorePercent}%</span>
                        <div class="match-score-bar"><div class="match-score-fill" style="width: ${scorePercent}%"></div></div>
                    </div>
                    <span class="badge ${statusClass}">${statusText}</span>
                </div>
                <div class="match-items">
                    <div class="match-item">
                        <div class="match-item-label">Lost</div>
                        <div class="match-item-title">${escapeHtml(lostItem.title || 'Unknown')}</div>
                    </div>
                    <div class="match-item">
                        <div class="match-item-label">Found</div>
                        <div class="match-item-title">${escapeHtml(foundItem.title || 'Unknown')}</div>
                    </div>
                </div>
            </div>
        `;
    }

    return `
        <div class="match-card">
            <div class="match-header">
                <div class="match-score">
                    <span class="match-score-value">${scorePercent}%</span>
                    <div class="match-score-bar"><div class="match-score-fill" style="width: ${scorePercent}%"></div></div>
                    <span style="font-size: 0.8rem; color: var(--text-muted);">match</span>
                </div>
                <span class="badge ${statusClass}">${statusText}</span>
            </div>

            <div class="match-items">
                <div class="match-item" onclick="viewItem(${m.lost_item_id})" style="cursor: pointer;">
                    <div class="match-item-label">🔴 Lost Item</div>
                    <div class="match-item-title">${escapeHtml(lostItem.title || 'Unknown')}</div>
                    <div class="match-item-meta">${escapeHtml(lostItem.location || '')} • ${formatDate(lostItem.date_time)}</div>
                </div>
                <div class="match-item" onclick="viewItem(${m.found_item_id})" style="cursor: pointer;">
                    <div class="match-item-label">🟢 Found Item</div>
                    <div class="match-item-title">${escapeHtml(foundItem.title || 'Unknown')}</div>
                    <div class="match-item-meta">${escapeHtml(foundItem.location || '')} • ${formatDate(foundItem.date_time)}</div>
                </div>
            </div>

            <div class="match-explanation">
                <strong>Why this matches:</strong> ${escapeHtml(m.explanation)}
            </div>

            <div class="match-factors">
                ${Object.entries(m.factor_scores || {}).map(([k, v]) => `
                    <span class="factor-chip">
                        <span class="factor-name">${k.replace(/_/g, ' ')}</span>
                        <span class="factor-value">${Math.round(v * 100)}%</span>
                    </span>
                `).join('')}
            </div>

            <div class="match-actions">
                <button class="btn btn-sm btn-secondary" onclick="updateMatchStatus(${m.id}, 'confirmed')">✓ Confirmed Match</button>
                <button class="btn btn-sm btn-outline" onclick="updateMatchStatus(${m.id}, 'rejected')">✗ Not a Match</button>
                <button class="btn btn-sm btn-primary" onclick="openContactRequest(${m.id})">📧 Contact / Claim</button>
            </div>
        </div>
    `;
}

function renderItemDetail(item) {
    const statusClass = item.type === 'lost' ? 'badge-lost' : 'badge-found';
    const statusText = item.type === 'lost' ? 'Lost' : 'Found';

    const imageHtml = item.image_path
        ? `<img src="${item.image_path}" alt="${escapeHtml(item.title)}" class="detail-image">`
        : `<div class="detail-image-placeholder">${getCategoryIcon(item.category)}</div>`;

    return `
        <div class="detail-header">
            ${imageHtml}
            <div class="detail-info">
                <div class="detail-title">${escapeHtml(item.title)}</div>
                <div class="detail-meta">
                    <span class="badge ${statusClass}">${statusText}</span>
                    <span>📍 ${escapeHtml(item.location)}</span>
                    <span>📅 ${formatDate(item.date_time)}</span>
                    ${item.category ? `<span>🏷️ ${escapeHtml(item.category)}</span>` : ''}
                </div>
            </div>
        </div>

        ${item.description ? `
        <div class="detail-section">
            <div class="detail-section-title">Description</div>
            <p>${escapeHtml(item.description)}</p>
        </div>
        ` : ''}

        <div class="detail-section">
            <div class="detail-section-title">AI Analysis</div>
            <div class="ai-analysis">
                <div class="ai-analysis-header">🤖 AI-Generated Tags</div>
                <div class="ai-analysis-grid">
                    <div class="ai-analysis-item">
                        <div class="ai-analysis-label">Object Type</div>
                        <div class="ai-analysis-value">${escapeHtml(item.object_type || 'Unknown')}</div>
                    </div>
                    <div class="ai-analysis-item">
                        <div class="ai-analysis-label">Color</div>
                        <div class="ai-analysis-value">${escapeHtml(item.color || 'Unknown')}</div>
                    </div>
                    <div class="ai-analysis-item">
                        <div class="ai-analysis-label">Brand</div>
                        <div class="ai-analysis-value">${escapeHtml(item.brand || 'Unknown')}</div>
                    </div>
                    <div class="ai-analysis-item">
                        <div class="ai-analysis-label">Category</div>
                        <div class="ai-analysis-value">${escapeHtml(item.category || 'Unknown')}</div>
                    </div>
                </div>
                ${item.characteristics && item.characteristics.length ? `
                <div style="margin-top: 12px;">
                    <div class="ai-analysis-label">Characteristics</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
                        ${item.characteristics.map(c => `<span class="tag">${escapeHtml(c)}</span>`).join('')}
                    </div>
                </div>
                ` : ''}
                ${item.distinctive_features && item.distinctive_features.length ? `
                <div style="margin-top: 12px;">
                    <div class="ai-analysis-label">Distinctive Features</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
                        ${item.distinctive_features.map(f => `<span class="tag tag-category">${escapeHtml(f)}</span>`).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">Details</div>
            <div class="detail-grid">
                <div class="detail-field">
                    <div class="detail-field-label">Location</div>
                    <div class="detail-field-value">${escapeHtml(item.location)}</div>
                </div>
                <div class="detail-field">
                    <div class="detail-field-label">Date/Time</div>
                    <div class="detail-field-value">${formatDate(item.date_time)}</div>
                </div>
                ${item.visible_text ? `
                <div class="detail-field">
                    <div class="detail-field-label">Visible Text</div>
                    <div class="detail-field-value">${escapeHtml(item.visible_text)}</div>
                </div>
                ` : ''}
            </div>
        </div>

        <div class="detail-section">
            <div class="detail-section-title">Actions</div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                <button class="btn btn-sm btn-primary" onclick="openContactRequestForItem(${item.id})">📧 Contact / Claim</button>
                <button class="btn btn-sm btn-outline" onclick="closeModal()">Close</button>
            </div>
        </div>
    `;
}

function getCategoryIcon(category) {
    const icons = { electronics: '📱', clothing: '👕', accessories: '👜', books: '📚', sports: '⚽', other: '📦' };
    return icons[category] || '📦';
}

async function loadDashboard() {
    try {
        const [stats, items, matches] = await Promise.all([
            api('/api/dashboard/stats'),
            api('/api/items?limit=6'),
            api('/api/matches?limit=3'),
        ]);
        state.dashboardStats = stats;
        state.items = items;
        state.matches = matches;
    } catch (e) {
        console.error('Failed to load dashboard:', e);
    }
}

async function loadItems(type) {
    try {
        state.items = await api(`/api/items?type=${type}&limit=100`);
    } catch (e) {
        console.error('Failed to load items:', e);
    }
}

async function loadMatches() {
    try {
        state.matches = await api('/api/matches?limit=100');
    } catch (e) {
        console.error('Failed to load matches:', e);
    }
}

async function viewItem(itemId) {
    try {
        const item = await api(`/api/items/${itemId}`);
        openModal(renderItemDetail(item));
    } catch (e) {
        showToast('Failed to load item', 'error');
    }
}

async function viewMatch(matchId) {
    try {
        const match = await api(`/api/matches/${matchId}`);
        openModal(renderMatchCard(match));
    } catch (e) {
        showToast('Failed to load match', 'error');
    }
}

async function updateMatchStatus(matchId, status) {
    try {
        await api(`/api/matches/${matchId}`, {
            method: 'PATCH',
            body: JSON.stringify({ status }),
        });
        showToast(`Match marked as ${status}`);
        closeModal();
        await loadMatches();
        render();
    } catch (e) {
        showToast('Failed to update match', 'error');
    }
}

function openContactRequest(matchId) {
    openModal(`
        <div class="page-header">
            <h1>📧 Contact / Claim</h1>
            <p>Send a message to the other party. Your contact info will be shared only after approval.</p>
        </div>
        <form onsubmit="submitContactRequest(event, ${matchId})">
            <div class="form-group">
                <label class="form-label">I am the</label>
                <select class="form-select" id="requesterType">
                    <option value="lost_owner">Owner of the lost item</option>
                    <option value="found_finder">Finder of the found item</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Message</label>
                <textarea class="form-textarea" id="contactMessage" placeholder="Write a message to help verify ownership..." required></textarea>
            </div>
            <div style="display: flex; gap: 12px;">
                <button type="submit" class="btn btn-primary">Send Request</button>
                <button type="button" class="btn btn-outline" onclick="closeModal()">Cancel</button>
            </div>
        </form>
    `);
}

function openContactRequestForItem(itemId) {
    showToast('Please use a match to contact the other party', 'error');
}

async function submitContactRequest(event, matchId) {
    event.preventDefault();
    const requesterType = document.getElementById('requesterType').value;
    const message = document.getElementById('contactMessage').value;

    try {
        await api('/api/matches/contact', {
            method: 'POST',
            body: JSON.stringify({ match_id: matchId, requester_type: requesterType, message }),
        });
        showToast('Contact request sent!');
        closeModal();
    } catch (e) {
        showToast('Failed to send request', 'error');
    }
}

function previewImage(input) {
    const file = input.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = e => {
        document.getElementById('filePreview').innerHTML = `
            <div class="file-preview">
                <img src="${e.target.result}" alt="Preview">
                <button type="button" class="file-preview-remove" onclick="clearImage()">×</button>
            </div>
        `;
    };
    reader.readAsDataURL(file);
}

function clearImage() {
    document.getElementById('imageInput').value = '';
    document.getElementById('filePreview').innerHTML = '';
}

async function submitReport(event, type) {
    event.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span>Analyzing with AI...</span>';

    try {
        const formData = new FormData();
        formData.append('type', type);
        formData.append('title', document.getElementById('title').value);
        formData.append('description', document.getElementById('description').value);
        formData.append('location', document.getElementById('location').value);
        formData.append('date_time', document.getElementById('date_time').value);

        const imageInput = document.getElementById('imageInput');
        if (imageInput.files[0]) {
            formData.append('image', imageInput.files[0]);
        }

        const item = await api('/api/items', {
            method: 'POST',
            body: formData,
        });

        showToast('Report submitted! AI is finding matches...');

        setTimeout(() => {
            closeModal();
            router.navigate('/matches');
        }, 1500);
    } catch (e) {
        showToast(e.message || 'Failed to submit report', 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span>Submit Report</span>';
    }
}

function filterItems(search, type) {
    const items = state.items.filter(i =>
        i.type === type && i.status === 'active' &&
        (!search || i.title.toLowerCase().includes(search.toLowerCase()) ||
         i.description.toLowerCase().includes(search.toLowerCase()))
    );

    document.getElementById('itemsList').innerHTML = items.length
        ? `<div class="items-grid">${items.map(item => renderItemCard(item)).join('')}</div>`
        : '<div class="empty-state"><div class="empty-state-icon">📭</div><div class="empty-state-text">No items found</div></div>';
}

function filterByCategory(category, type) {
    const items = state.items.filter(i =>
        i.type === type && i.status === 'active' &&
        (!category || i.category === category)
    );

    document.getElementById('itemsList').innerHTML = items.length
        ? `<div class="items-grid">${items.map(item => renderItemCard(item)).join('')}</div>`
        : '<div class="empty-state"><div class="empty-state-icon">📭</div><div class="empty-state-text">No items found</div></div>';
}

function filterMatches(status) {
    const matches = state.matches.filter(m => !status || m.status === status);
    document.getElementById('matchesList').innerHTML = matches.length
        ? matches.map(m => renderMatchCard(m)).join('')
        : '<div class="empty-state"><div class="empty-state-icon">🔗</div><div class="empty-state-text">No matches found</div></div>';
}

async function render() {
    const app = document.getElementById('app');
    const route = router.resolve();

    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('active', link.dataset.route === route);
    });

    app.innerHTML = '<div class="loading-screen"><div class="spinner"></div><p>Loading...</p></div>';

    try {
        switch (route) {
            case 'dashboard':
                await loadDashboard();
                app.innerHTML = renderDashboard();
                break;
            case 'report-lost':
                app.innerHTML = renderReportForm('lost');
                break;
            case 'report-found':
                app.innerHTML = renderReportForm('found');
                break;
            case 'browse-lost':
                await loadItems('lost');
                app.innerHTML = renderBrowse('lost');
                break;
            case 'browse-found':
                await loadItems('found');
                app.innerHTML = renderBrowse('found');
                break;
            case 'matches':
                await loadMatches();
                app.innerHTML = renderMatches();
                break;
            default:
                await loadDashboard();
                app.innerHTML = renderDashboard();
        }
    } catch (e) {
        app.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><div class="empty-state-text">Something went wrong</div><div class="empty-state-hint">${escapeHtml(e.message)}</div></div>`;
    }
}

document.getElementById('modalClose').addEventListener('click', closeModal);
document.getElementById('modalOverlay').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal();
});

document.getElementById('navToggle').addEventListener('click', () => {
    document.querySelector('.nav-links').classList.toggle('active');
});

window.addEventListener('hashchange', render);

document.addEventListener('DOMContentLoaded', () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    const dateInput = document.getElementById('date_time');
    if (dateInput) {
        dateInput.value = now.toISOString().slice(0, 16);
    }
    render();
});
