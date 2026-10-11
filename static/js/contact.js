// MarketMind Contact and Feedback Controller
document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('contactForm');
  const alertBox = document.getElementById('contactAlert');
  const submitBtn = document.getElementById('submitFeedbackBtn');
  const feedbackList = document.getElementById('feedbackList');

  form.addEventListener('submit', function(e) {
    e.preventDefault();

    const name = document.getElementById('contactName').value.trim();
    const email = document.getElementById('contactEmail').value.trim();
    const category = document.getElementById('contactCategory').value;
    const rating = document.getElementById('contactRating').value;
    const subject = document.getElementById('contactSubject').value.trim();
    const message = document.getElementById('contactMessage').value.trim();

    if (!name || !email || !subject || !message) {
      alertBox.className = 'alert alert-danger';
      alertBox.textContent = 'Please fill out all required fields marked with an asterisk (*).';
      alertBox.classList.remove('d-none');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-1"></i> Saving to Database...';

    fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        email: email,
        category: category,
        rating: parseInt(rating),
        subject: subject,
        message: message
      })
    })
    .then(res => res.json())
    .then(data => {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane me-2"></i> Save Feedback to Database';

      if (data.success) {
        alertBox.className = 'alert alert-success';
        alertBox.innerHTML = `<i class="fa-solid fa-circle-check me-1"></i> ${data.message}`;
        alertBox.classList.remove('d-none');

        // Prepend new feedback card
        const card = document.createElement('div');
        card.className = 'p-3 bg-light rounded-3 border';
        card.innerHTML = `
          <div class="d-flex justify-content-between align-items-start mb-1">
            <div>
              <strong class="text-dark small">${escapeHtml(name)}</strong>
              <span class="text-muted" style="font-size: 0.75rem;">&bull; ${escapeHtml(category)}</span>
            </div>
            <span class="badge bg-warning text-dark small">&starf; ${rating}/5</span>
          </div>
          <div class="fw-semibold small text-primary mb-1">${escapeHtml(subject)}</div>
          <p class="text-muted small mb-1">${escapeHtml(message)}</p>
          <div class="text-muted" style="font-size: 0.72rem;"><i class="fa-solid fa-calendar-day me-1"></i> Just now</div>
        `;
        feedbackList.prepend(card);

        form.reset();
        MarketMind.showToast("Feedback Saved", "Thank you for your academic review!", "success");
      } else {
        alertBox.className = 'alert alert-danger';
        alertBox.textContent = data.message;
        alertBox.classList.remove('d-none');
      }
    })
    .catch(err => {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane me-2"></i> Save Feedback to Database';
      alertBox.className = 'alert alert-danger';
      alertBox.textContent = err.toString();
      alertBox.classList.remove('d-none');
    });
  });

  function escapeHtml(str) {
    return str.replace(/[&<>'"]/g, 
      tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
  }
});
