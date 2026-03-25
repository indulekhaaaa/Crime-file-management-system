/* Crime Record Management System — Main JS */

// ---- Auto-hide alerts ----
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.auto-dismiss');
    alerts.forEach(el => {
        setTimeout(() => {
            el.style.transition = 'opacity .5s';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 500);
        }, 3500);
    });

    // ---- Active nav highlight ----
    const path = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(item => {
        const href = item.getAttribute('href');
        if (href && (path === href || (href !== '/' && path.startsWith(href)))) {
            item.classList.add('active');
        }
    });

    // ---- Live clock ----
    const clockEl = document.getElementById('live-clock');
    if (clockEl) {
        const updateClock = () => {
            const now = new Date();
            clockEl.textContent = now.toLocaleString('en-IN', {
                day: '2-digit', month: 'short', year: 'numeric',
                hour: '2-digit', minute: '2-digit', second: '2-digit'
            });
        };
        updateClock();
        setInterval(updateClock, 1000);
    }

    // ---- Confirm delete ----
    document.querySelectorAll('.confirm-delete').forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!confirm('Are you sure you want to delete this record? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // ---- Dashboard charts ----
    if (typeof Chart !== 'undefined') {
        initDashboardCharts();
    }
});

// ---- Chart.js setup ----
function initDashboardCharts() {
    const crimeCtx = document.getElementById('crimeChart');
    const statusCtx = document.getElementById('statusChart');

    if (crimeCtx) {
        fetch('/api/crime-stats')
            .then(r => r.json())
            .then(data => {
                new Chart(crimeCtx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'FIRs Registered',
                            data: data.data,
                            backgroundColor: 'rgba(179,0,0,0.7)',
                            borderColor: '#ff3333',
                            borderWidth: 1,
                            borderRadius: 4,
                        }]
                    },
                    options: chartOptions('Crime Type Distribution')
                });
            });
    }

    if (statusCtx) {
        fetch('/api/status-stats')
            .then(r => r.json())
            .then(data => {
                const COLORS = ['#ff3333','#ffc107','#28a745','#6c757d'];
                new Chart(statusCtx, {
                    type: 'doughnut',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            data: data.data,
                            backgroundColor: COLORS.slice(0, data.data.length),
                            borderColor: '#111',
                            borderWidth: 2,
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: { color: '#ccc', font: { size: 11 } }
                            }
                        }
                    }
                });
            });
    }
}

function chartOptions(title) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: { display: false }
        },
        scales: {
            x: {
                ticks: { color: '#999', font: { size: 11 } },
                grid:  { color: 'rgba(255,255,255,0.05)' }
            },
            y: {
                ticks: { color: '#999', font: { size: 11 } },
                grid:  { color: 'rgba(255,255,255,0.05)' },
                beginAtZero: true
            }
        }
    };
}
