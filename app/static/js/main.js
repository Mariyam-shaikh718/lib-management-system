function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// Auto-dismiss alerts after 4 seconds
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.alert').forEach(function(alert) {
    setTimeout(function() {
      if (alert.parentNode) alert.remove();
    }, 4000);
  });
});

// Confirm forms
document.querySelectorAll('[data-confirm]').forEach(function(el) {
  el.addEventListener('click', function(e) {
    if (!confirm(this.dataset.confirm)) e.preventDefault();
  });
});