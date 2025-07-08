// static/js/main.js

// 1) Purchase interactivity & loading
const form = document.getElementById('purchase-form');
const payBtn = form.querySelector('.pay-btn');
const details = document.getElementById('purchase-details');
const phoneInput = document.getElementById('phone');
const phoneError = document.getElementById('phone-error');

document.querySelectorAll('.pkg-circle input').forEach(radio => {
  radio.addEventListener('change', () => {
    details.classList.add('visible');
    document.querySelectorAll('.pkg-circle').forEach(lbl => lbl.classList.remove('selected'));
    radio.closest('label.pkg-circle').classList.add('selected');
  });
});

form.addEventListener('submit', e => {
  if (!phoneInput.checkValidity()) {
    e.preventDefault();
    phoneError.style.display = 'block';
    phoneInput.focus();
    return;
  }
  payBtn.disabled = true;
  payBtn.classList.add('loading');
  payBtn.textContent = 'Processing';
});

// phone input inline validation
phoneInput.addEventListener('input', () => {
  phoneError.style.display = phoneInput.checkValidity() ? 'none' : 'block';
});

// 2) Mpesa code inline validation
const codeInput = document.getElementById('mpesa_code');
const codeError = document.getElementById('code-error');
if (codeInput) {
  codeInput.addEventListener('input', () => {
    codeError.style.display = codeInput.checkValidity() ? 'none' : 'block';
  });
}

// 3) Flash-toasts
document.querySelectorAll('#flashes li').forEach(li => {
  const cat = li.dataset.category;
  const msg = li.textContent;
  const toast = document.createElement('div');
  toast.className = `toast ${cat}`;
  toast.textContent = msg;
  document.getElementById('toasts').appendChild(toast);
  setTimeout(() => toast.classList.add('hide'), 4000);
  toast.addEventListener('transitionend', () => toast.remove());
});

// 4) Tooltips
document.querySelectorAll('.info-icon').forEach(icon => {
  icon.addEventListener('mouseenter', () => {
    const tip = document.createElement('div');
    tip.className = 'tooltip';
    tip.textContent = icon.dataset.tooltip;
    icon.appendChild(tip);
  });
  icon.addEventListener('mouseleave', () => {
    icon.querySelector('.tooltip')?.remove();
  });
});
