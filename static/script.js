// Load form fragment from /form and inject into DOM
document.getElementById('btn-load-form').addEventListener('click', async () => {
  const res = await fetch('/form');
  const html = await res.text();
  document.getElementById('form-container').innerHTML = html;
});

// Submit form data to /submit
document.getElementById('btn-submit').addEventListener('click', async () => {
  const form = document.querySelector('#form-container form');
  const data = new FormData(form);
  const res = await fetch('/submit', { method: 'POST', body: data });
  const msg = await res.text();
  document.getElementById('results').textContent = msg;
});

// Trigger analysis at /analyze
document.getElementById('btn-analyze').addEventListener('click', async () => {
  const res = await fetch('/analyze');
  const msg = await res.text();
  document.getElementById('results').textContent = msg;
});

// Fetch and display input data from /view/input
document.getElementById('btn-view-input').addEventListener('click', async () => {
  const res = await fetch('/view/input');
  const data = await res.json();
  document.getElementById('results').textContent = JSON.stringify(data, null, 2);
});

// Fetch and display profile from /view/profile
document.getElementById('btn-view-profile').addEventListener('click', async () => {
  const res = await fetch('/view/profile');
  const data = await res.json();
  document.getElementById('results').textContent = JSON.stringify(data, null, 2);
});