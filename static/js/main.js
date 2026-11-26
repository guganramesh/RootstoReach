/* ─── Flash messages auto-dismiss ─── */
document.querySelectorAll('.alert-close').forEach(btn => {
  btn.addEventListener('click', () => btn.closest('.alert').remove());
});
setTimeout(() => {
  document.querySelectorAll('.alert').forEach(a => {
    a.style.transition = 'opacity 0.5s';
    a.style.opacity = '0';
    setTimeout(() => a.remove(), 500);
  });
}, 4000);

/* ─── Navbar dropdown ─── */
const userMenuBtn = document.getElementById('userMenuBtn');
const userDropdown = document.getElementById('userDropdown');
if (userMenuBtn && userDropdown) {
  userMenuBtn.addEventListener('click', e => {
    e.stopPropagation();
    userDropdown.classList.toggle('open');
  });
  document.addEventListener('click', () => userDropdown.classList.remove('open'));
}

/* ─── Mobile Nav ─── */
const hamburger = document.getElementById('hamburger');
const mobileNav = document.getElementById('mobileNav');
if (hamburger && mobileNav) {
  hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    mobileNav.classList.toggle('open');
  });
}

/* ─── Scroll to top ─── */
const scrollTopBtn = document.getElementById('scrollTop');
if (scrollTopBtn) {
  window.addEventListener('scroll', () => {
    scrollTopBtn.classList.toggle('visible', window.scrollY > 300);
  });
  scrollTopBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

/* ─── Animate on scroll ─── */
const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('animate-fadeInUp');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });
document.querySelectorAll('.feature-card, .step-card, .knowledge-card, .product-card, .testimonial-card, .post-card, .market-card, .stat-card')
  .forEach(el => observer.observe(el));

/* ─── Sidebar toggle (dashboard) ─── */
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');
if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    sidebarOverlay.classList.toggle('open');
  });
  sidebarOverlay?.addEventListener('click', () => {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('open');
  });
}

/* ─── Password toggle ─── */
document.querySelectorAll('.pwd-eye').forEach(eye => {
  eye.addEventListener('click', () => {
    const input = eye.previousElementSibling;
    if (input && input.type) {
      input.type = input.type === 'password' ? 'text' : 'password';
      eye.textContent = input.type === 'password' ? '👁' : '🙈';
    }
  });
});

/* ─── Skill tags toggle ─── */
document.querySelectorAll('.skill-tag').forEach(tag => {
  tag.addEventListener('click', () => {
    tag.classList.toggle('selected');
    const input = document.getElementById('skillsInput');
    if (input) {
      const selected = [...document.querySelectorAll('.skill-tag.selected')].map(t => t.dataset.skill);
      input.value = selected.join(', ');
    }
  });
});

/* ─── Image upload preview ─── */
const imageInput = document.getElementById('imageUpload');
const uploadPreview = document.getElementById('uploadPreview');
if (imageInput && uploadPreview) {
  imageInput.addEventListener('change', () => {
    uploadPreview.innerHTML = '';
    [...imageInput.files].slice(0, 5).forEach(file => {
      const reader = new FileReader();
      reader.onload = e => {
        const img = document.createElement('img');
        img.src = e.target.result;
        img.className = 'upload-preview-img';
        uploadPreview.appendChild(img);
      };
      reader.readAsDataURL(file);
    });
  });
}

/* ─── Upload zone drag & drop ─── */
const uploadZone = document.getElementById('uploadZone');
if (uploadZone) {
  ['dragover', 'dragenter'].forEach(e => uploadZone.addEventListener(e, ev => {
    ev.preventDefault(); uploadZone.classList.add('drag-over');
  }));
  ['dragleave', 'drop'].forEach(e => uploadZone.addEventListener(e, ev => {
    ev.preventDefault(); uploadZone.classList.remove('drag-over');
    if (e === 'drop' && imageInput) {
      imageInput.files = ev.dataTransfer.files;
      imageInput.dispatchEvent(new Event('change'));
    }
  }));
  uploadZone.addEventListener('click', () => imageInput?.click());
}

/* ─── Quantity selector ─── */
const qtyInput = document.getElementById('qtyInput');
document.querySelectorAll('.qty-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    if (!qtyInput) return;
    let val = parseInt(qtyInput.value) || 1;
    val = btn.dataset.action === 'plus' ? val + 1 : Math.max(1, val - 1);
    qtyInput.value = val;
  });
});

/* ─── Settings tab switching ─── */
document.querySelectorAll('.settings-nav-item').forEach(item => {
  item.addEventListener('click', () => {
    const target = item.dataset.panel;
    document.querySelectorAll('.settings-nav-item').forEach(i => i.classList.remove('active'));
    document.querySelectorAll('.settings-section').forEach(s => s.classList.add('hidden'));
    item.classList.add('active');
    const panel = document.getElementById(target);
    if (panel) panel.classList.remove('hidden');
  });
});

/* ─── Notification count ─── */
async function updateNotifCount() {
  try {
    const res = await fetch('/api/notifications');
    const data = await res.json();
    const badge = document.getElementById('notifBadge');
    if (badge) badge.style.display = data.count > 0 ? 'block' : 'none';
  } catch (_) {}
}
if (document.getElementById('notifBadge')) {
  updateNotifCount();
  setInterval(updateNotifCount, 30000);
}

/* ─── Auto-scroll chat ─── */
const chatMessages = document.getElementById('chatMessages');
if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;

/* ─── Filter buttons ─── */
document.querySelectorAll('.filter-btn[data-filter]').forEach(btn => {
  btn.addEventListener('click', () => {
    const url = new URL(window.location.href);
    url.searchParams.set('category', btn.dataset.filter);
    window.location.href = url.toString();
  });
});

/* ─── Counter animation ─── */
function animateCounter(el) {
  const target = parseInt(el.dataset.target || el.textContent.replace(/[^0-9]/g, ''));
  if (isNaN(target)) return;
  let current = 0;
  const step = target / 40;
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = Math.floor(current).toLocaleString();
    if (current >= target) clearInterval(timer);
  }, 30);
}
const counterObs = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      animateCounter(entry.target);
      counterObs.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });
document.querySelectorAll('.stat-value[data-target]').forEach(el => counterObs.observe(el));
