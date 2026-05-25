// Configuration
const API_BASE = '/api';

// State management
let state = {
    activeTab: 'overview',
    users: [],
    contests: [],
    withdrawals: []
};

// Elements
const el = {
    tabs: document.querySelectorAll('.menu-item'),
    panels: document.querySelectorAll('.tab-panel'),
    pageTitle: document.getElementById('page-title'),
    pageSubtitle: document.getElementById('page-subtitle'),
    btnRefresh: document.getElementById('btn-refresh'),
    toast: document.getElementById('toast'),
    
    // Stats
    statUsers: document.getElementById('stat-users'),
    statDeposits: document.getElementById('stat-deposits'),
    statContests: document.getElementById('stat-contests'),
    statWinnings: document.getElementById('stat-winnings'),
    statRevenue: document.getElementById('stat-revenue'),
    
    // Forms
    quickContestForm: document.getElementById('quick-contest-form'),
    
    // Tables
    usersTable: document.getElementById('users-table-body'),
    contestsTable: document.getElementById('contests-table-body'),
    withdrawalsTable: document.getElementById('withdrawals-table-body'),
    userSearch: document.getElementById('user-search')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    setupTabNavigation();
    setupEventHandlers();
    loadDashboardData();
    
    // Automatically poll stats every 30 seconds
    setInterval(loadDashboardData, 30000);
});

// Toast Notifications
function showToast(message, isError = false) {
    el.toast.innerText = message;
    el.toast.style.borderLeftColor = isError ? 'var(--error)' : 'var(--primary)';
    el.toast.classList.add('show');
    
    setTimeout(() => {
        el.toast.classList.remove('show');
    }, 3500);
}

// Tab Navigation
function setupTabNavigation() {
    el.tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');
            if (state.activeTab === targetTab) return;
            
            // Update active menu items
            el.tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update active panel
            el.panels.forEach(p => p.classList.remove('active'));
            document.getElementById(`panel-${targetTab}`).classList.add('active');
            
            state.activeTab = targetTab;
            updateHeaders(targetTab);
            
            // Trigger specific loading for tab
            loadTabSpecificData(targetTab);
        });
    });
}

function updateHeaders(tab) {
    switch (tab) {
        case 'overview':
            el.pageTitle.innerText = "Platform Overview";
            el.pageSubtitle.innerText = "Real-time statistics & business metrics";
            break;
        case 'users':
            el.pageTitle.innerText = "User Management";
            el.pageSubtitle.innerText = "View user records, wallet balances, and issue bans";
            break;
        case 'contests':
            el.pageTitle.innerText = "Contest Engine";
            el.pageSubtitle.innerText = "Monitor active game lobbies and track players";
            break;
        case 'withdrawals':
            el.pageTitle.innerText = "Withdrawal Controls";
            el.pageSubtitle.innerText = "Verify KYC PAN logs and approve payout requests";
            break;
        case 'notifications':
            el.pageTitle.innerText = "Notification Center";
            el.pageSubtitle.innerText = "Send custom Firebase push messages directly to client devices";
            break;
    }
}

// Event Handlers Setup
function setupEventHandlers() {
    el.btnRefresh.addEventListener('click', () => {
        el.btnRefresh.classList.add('spinning');
        loadDashboardData().then(() => {
            setTimeout(() => el.btnRefresh.classList.remove('spinning'), 500);
            showToast("System metrics synchronized.");
        });
    });
    
    // Quick Contest Form Submission
    if (el.quickContestForm) {
        el.quickContestForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const title = document.getElementById('c-title').value;
            const entryFee = parseFloat(document.getElementById('c-fee').value);
            const totalSlots = parseInt(document.getElementById('c-slots').value);
            const prizePool = parseFloat(document.getElementById('c-pool').value);
            
            // Set start time to 30 mins in future
            const startTime = new Date(Date.now() + 30 * 60 * 1000).toISOString();
            
            try {
                const response = await fetch(`${API_BASE}/admin/contests`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title,
                        entry_fee: entryFee,
                        total_slots: totalSlots,
                        prize_pool: prizePool,
                        start_time: startTime
                    })
                });
                
                if (!response.ok) throw new Error(await response.text());
                
                showToast("Contest created and deployed successfully!");
                el.quickContestForm.reset();
                
                // Reload data if on overview/contests tab
                loadDashboardData();
            } catch (err) {
                console.error(err);
                showToast("Failed to create contest: " + err.message, true);
            }
        });
    }
    
    // Push Notification Recipient toggle
    const recipientType = document.getElementById('push-recipient-type');
    const userIdGroup = document.getElementById('push-user-id-group');
    if (recipientType && userIdGroup) {
        recipientType.addEventListener('change', (e) => {
            if (e.target.value === 'user') {
                userIdGroup.style.display = 'block';
            } else {
                userIdGroup.style.display = 'none';
            }
        });
    }

    // Send Push Notification Click
    const btnSendPush = document.getElementById('btn-send-push');
    if (btnSendPush) {
        btnSendPush.addEventListener('click', async () => {
            const type = document.getElementById('push-recipient-type').value;
            const title = document.getElementById('push-title').value.trim();
            const body = document.getElementById('push-body').value.trim();
            
            if (!title || !body) {
                showToast("Please enter both title and body.", true);
                return;
            }
            
            btnSendPush.disabled = true;
            btnSendPush.innerText = "Sending...";
            
            try {
                let endpoint, payload;
                if (type === 'user') {
                    const userId = parseInt(document.getElementById('push-user-id').value);
                    if (isNaN(userId)) {
                        showToast("Please enter a valid User ID.", true);
                        btnSendPush.disabled = false;
                        btnSendPush.innerText = "Send Notification";
                        return;
                    }
                    endpoint = `${API_BASE}/admin/notifications/send-user`;
                    payload = { user_id: userId, title, body };
                } else {
                    endpoint = `${API_BASE}/admin/notifications/send-all`;
                    payload = { title, body };
                }
                
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (!res.ok) {
                    const errorText = await res.text();
                    throw new Error(errorText || "Server error");
                }
                
                showToast("Notification request processed!");
                document.getElementById('push-title').value = '';
                document.getElementById('push-body').value = '';
                if (type === 'user') {
                    document.getElementById('push-user-id').value = '';
                }
            } catch (err) {
                showToast("Error: " + err.message, true);
            } finally {
                btnSendPush.disabled = false;
                btnSendPush.innerText = "Send Notification";
            }
        });
    }
    
    // Search Filter
    el.userSearch.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        filterUsersTable(query);
    });
}

// Data loading
async function loadDashboardData() {
    try {
        // Fetch stats
        const statsRes = await fetch(`${API_BASE}/admin/stats`);
        if (!statsRes.ok) throw new Error("Failed to load statistics.");
        const stats = await statsRes.json();
        
        // Render stats
        el.statUsers.innerText = stats.total_users;
        el.statDeposits.innerText = `₹${stats.total_deposits.toFixed(2)}`;
        el.statContests.innerText = stats.active_contests;
        el.statWinnings.innerText = `₹${stats.total_winnings_paid.toFixed(2)}`;
        el.statRevenue.innerText = `₹${stats.total_revenue.toFixed(2)}`;
        
        // Change color based on positive/negative revenue
        if (stats.total_revenue < 0) {
            el.statRevenue.style.color = 'var(--error)';
        } else {
            el.statRevenue.style.color = 'var(--success)';
        }
        
        // Load active tab data
        loadTabSpecificData(state.activeTab);
    } catch (err) {
        console.error(err);
        showToast(err.message, true);
    }
}

function loadTabSpecificData(tab) {
    switch (tab) {
        case 'users':
            loadUsers();
            break;
        case 'contests':
            loadContests();
            break;
        case 'withdrawals':
            loadWithdrawals();
            break;
    }
}

// 1. Users Operations
async function loadUsers() {
    try {
        const res = await fetch(`${API_BASE}/admin/users`);
        if (!res.ok) throw new Error("Failed to load users list.");
        state.users = await res.json();
        renderUsersTable(state.users);
    } catch (err) {
        showToast(err.message, true);
    }
}

function renderUsersTable(usersList) {
    if (usersList.length === 0) {
        el.usersTable.innerHTML = `<tr><td colspan="6" class="table-placeholder">No accounts registered yet.</td></tr>`;
        return;
    }
    
    el.usersTable.innerHTML = usersList.map(u => {
        const banBtn = u.is_banned 
            ? `<button class="btn btn-action btn-unban" onclick="toggleBan(${u.id}, false)">Unban User</button>`
            : `<button class="btn btn-action btn-ban" onclick="toggleBan(${u.id}, true)">Ban User</button>`;
            
        return `
            <tr>
                <td>${u.id}</td>
                <td>
                    <div class="user-cell">
                        <span class="user-name">${u.name || 'Anonymous User'}</span>
                        <span class="user-phone">${u.phone} (Code: ${u.referral_code})</span>
                    </div>
                </td>
                <td>
                    <div class="balance-grid">
                        <div class="bal-item">
                            <div class="bal-lbl">Deposit</div>
                            <div class="bal-val dep">₹${u.deposit_balance.toFixed(2)}</div>
                        </div>
                        <div class="bal-item">
                            <div class="bal-lbl">Winnings</div>
                            <div class="bal-val win">₹${u.winning_balance.toFixed(2)}</div>
                        </div>
                        <div class="bal-item">
                            <div class="bal-lbl">Bonus</div>
                            <div class="bal-val bon">₹${u.bonus_balance.toFixed(2)}</div>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="badge ${u.kyc_status === 'VERIFIED' ? 'badge-success' : 'badge-warning'}">
                        ${u.kyc_status}
                    </span>
                </td>
                <td>${u.referred_by ? `<span class="badge badge-info">${u.referred_by}</span>` : '<span class="text-muted">-</span>'}</td>
                <td>
                    <div style="display: flex; gap: 8px;">
                        ${banBtn}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function filterUsersTable(query) {
    const filtered = state.users.filter(u => 
        u.phone.includes(query) || 
        (u.name && u.name.toLowerCase().includes(query)) ||
        u.referral_code.toLowerCase().includes(query)
    );
    renderUsersTable(filtered);
}

async function toggleBan(userId, ban) {
    try {
        const res = await fetch(`${API_BASE}/admin/users/${userId}/ban?ban=${ban}`, {
            method: 'POST'
        });
        if (!res.ok) throw new Error("Failed to ban/unban user.");
        
        showToast(ban ? "User account has been banned." : "User account active.");
        loadUsers();
    } catch (err) {
        showToast(err.message, true);
    }
}

// 2. Contests Operations
async function loadContests() {
    try {
        const res = await fetch(`${API_BASE}/contests`);
        if (!res.ok) throw new Error("Failed to load contests.");
        state.contests = await res.json();
        renderContestsTable(state.contests);
    } catch (err) {
        showToast(err.message, true);
    }
}

function renderContestsTable(contestsList) {
    if (contestsList.length === 0) {
        el.contestsTable.innerHTML = `<tr><td colspan="8" class="table-placeholder">No contests defined yet.</td></tr>`;
        return;
    }
    
    el.contestsTable.innerHTML = contestsList.map(c => {
        let statusBadge = 'badge-warning';
        if (c.status === 'ACTIVE') statusBadge = 'badge-success';
        if (c.status === 'COMPLETED') statusBadge = 'badge-info';
        
        const startTimeStr = new Date(c.start_time).toLocaleString();
        
        const actionBtn = c.status !== 'COMPLETED'
            ? `<button class="btn btn-action btn-unban" onclick="completeContest(${c.id})">Complete</button>`
            : `<span class="text-muted" style="font-size:12px;">Payout Done</span>`;

        return `
            <tr>
                <td>${c.id}</td>
                <td><strong style="font-size:14px;">${c.title}</strong></td>
                <td>₹${c.entry_fee.toFixed(2)}</td>
                <td>
                    <div class="user-cell">
                        <span>${c.joined_slots} / ${c.total_slots} filled</span>
                        <div style="background-color: rgba(255,255,255,0.05); width:120px; height:4px; border-radius:2px; margin-top:4px; overflow:hidden;">
                            <div style="background:var(--primary); height:100%; width: ${(c.joined_slots/c.total_slots)*100}%"></div>
                        </div>
                    </div>
                </td>
                <td><strong>₹${c.prize_pool.toFixed(2)}</strong></td>
                <td>${startTimeStr}</td>
                <td><span class="badge ${statusBadge}">${c.status}</span></td>
                <td>
                    <div style="display:flex; gap:8px;">
                        ${actionBtn}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// 3. Payout/Withdrawal Operations
async function loadWithdrawals() {
    try {
        const res = await fetch(`${API_BASE}/admin/withdrawals`);
        if (!res.ok) throw new Error("Failed to load withdrawals.");
        state.withdrawals = await res.json();
        renderWithdrawalsTable(state.withdrawals);
    } catch (err) {
        showToast(err.message, true);
    }
}

function renderWithdrawalsTable(withdrawalsList) {
    if (withdrawalsList.length === 0) {
        el.withdrawalsTable.innerHTML = `<tr><td colspan="6" class="table-placeholder">No withdrawals requested.</td></tr>`;
        return;
    }
    
    el.withdrawalsTable.innerHTML = withdrawalsList.map(w => {
        const dateStr = new Date(w.created_at).toLocaleString();
        
        let actions = '<span class="text-muted">-</span>';
        if (w.status === 'PENDING') {
            actions = `
                <div style="display:flex; gap: 8px;">
                    <button class="btn btn-action btn-unban" onclick="approveWithdrawal(${w.id}, true)">Approve</button>
                    <button class="btn btn-action btn-ban" onclick="approveWithdrawal(${w.id}, false)">Reject</button>
                </div>
            `;
        }
        
        let statusClass = 'badge-warning';
        if (w.status === 'SUCCESS') statusClass = 'badge-success';
        if (w.status === 'FAILED') statusClass = 'badge-error';
        
        return `
            <tr>
                <td>${w.id}</td>
                <td>User #${w.user_id}</td>
                <td><strong style="color:var(--error)">₹${w.amount.toFixed(2)}</strong></td>
                <td>${dateStr}</td>
                <td><span class="badge ${statusClass}">${w.status}</span></td>
                <td>${actions}</td>
            </tr>
        `;
    }).join('');
}

async function approveWithdrawal(txId, approve) {
    try {
        const res = await fetch(`${API_BASE}/admin/withdrawals/${txId}/approve?approve=${approve}`, {
            method: 'POST'
        });
        if (!res.ok) throw new Error("Failed to process withdrawal action.");
        
        showToast(approve ? "Withdrawal payout approved!" : "Withdrawal rejected & refunded.");
        loadDashboardData();
    } catch (err) {
        showToast(err.message, true);
    }
}

async function completeContest(contestId) {
    if (!confirm("Are you sure you want to complete this contest and pay out the winners?")) return;
    try {
        const res = await fetch(`${API_BASE}/admin/contests/${contestId}/complete`, {
            method: 'POST'
        });
        if (!res.ok) throw new Error(await res.text());
        showToast("Contest completed and payouts distributed!");
        loadDashboardData();
    } catch (err) {
        showToast("Error completing contest: " + err.message, true);
    }
}
