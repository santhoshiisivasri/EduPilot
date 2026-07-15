/**
 * EduPilot – Main JavaScript
 * Global utilities, sidebar, dark mode, animations
 */

// ─── Dark Mode ──────────────────────────────────────────────
function toggleDarkMode() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  const newTheme = isDark ? 'light' : 'dark';
  html.setAttribute('data-theme', newTheme);
  localStorage.setItem('edupilot-theme', newTheme);

  // Update dark mode toggle UI
  const toggleThumb = document.getElementById('toggleThumb');
  if (toggleThumb) {
    toggleThumb.style.left = isDark ? '3px' : '27px';
    toggleThumb.previousElementSibling.style.background = isDark ? 'var(--border)' : 'var(--gradient-primary)';
  }

  // Persist to server
  fetch('/settings/update', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dark_mode: !isDark })
  }).catch(() => {});
}

// Apply saved theme on load
(function() {
  const saved = localStorage.getItem('edupilot-theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
})();

// ─── Sidebar ────────────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (!sidebar) return;
  sidebar.classList.toggle('open');
  if (overlay) overlay.classList.toggle('active');
}

function closeSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  if (sidebar) sidebar.classList.remove('open');
  if (overlay) overlay.classList.remove('active');
}

// Close sidebar on Escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeSidebar();
});

// ─── Animate on scroll ──────────────────────────────────────
const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -50px 0px' };

const animObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
      animObserver.unobserve(entry.target);
    }
  });
}, observerOptions);

document.addEventListener('DOMContentLoaded', () => {
  // Animate stat cards
  document.querySelectorAll('.stat-card, .glass-card').forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(16px)';
    el.style.transition = `opacity 0.4s ease ${i * 0.05}s, transform 0.4s ease ${i * 0.05}s`;
    animObserver.observe(el);
  });

  // Animate progress bars
  setTimeout(() => {
    document.querySelectorAll('.progress-bar-fill').forEach(bar => {
      const targetWidth = bar.style.width;
      bar.style.width = '0%';
      requestAnimationFrame(() => {
        bar.style.transition = 'width 1.2s cubic-bezier(0.4, 0, 0.2, 1)';
        bar.style.width = targetWidth;
      });
    });
  }, 300);
});

// ─── Progress Rings ──────────────────────────────────────────
function animateProgressRing(elementId, percentage) {
  const ring = document.getElementById(elementId);
  if (!ring) return;

  const radius = parseFloat(ring.getAttribute('r'));
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - percentage / 100);

  ring.style.strokeDasharray = circumference;
  ring.style.strokeDashoffset = circumference; // Start from 0

  requestAnimationFrame(() => {
    ring.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
    ring.style.strokeDashoffset = offset;
  });
}

// Auto-animate visible rings
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.progress-ring-fill').forEach(ring => {
    const originalOffset = ring.style.strokeDashoffset;
    const circumference = parseFloat(ring.style.strokeDasharray || '0');
    const percentage = circumference > 0 ? ((1 - parseFloat(originalOffset) / circumference) * 100) : 0;
    ring.style.strokeDashoffset = circumference;
    setTimeout(() => {
      ring.style.transition = 'stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1)';
      ring.style.strokeDashoffset = originalOffset;
    }, 500);
  });
});

// ─── Counter Animation ───────────────────────────────────────
function animateCounter(element, target, duration = 1500) {
  const start = 0;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = Math.round(start + (target - start) * eased);
    if (progress < 1) requestAnimationFrame(update);
  }

  requestAnimationFrame(update);
}

// ─── Toast Notification ──────────────────────────────────────
function showToastGlobal(message, type = 'success') {
  const container = document.querySelector('.flash-container') || (() => {
    const c = document.createElement('div');
    c.className = 'flash-container';
    document.body.appendChild(c);
    return c;
  })();

  const toast = document.createElement('div');
  toast.className = `flash-message ${type}`;
  toast.innerHTML = `
    <i class="bi bi-${type === 'success' ? 'check-circle-fill text-success' : 'info-circle-fill text-info'}"></i>
    <span style="flex:1;font-size:.875rem;color:var(--text);">${message}</span>
    <button onclick="this.closest('.flash-message').remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;">✕</button>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'slideInRight 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
