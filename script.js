// Load form fragment once the DOM content is loaded
document.addEventListener('DOMContentLoaded', async () => {
  const res = await fetch('/form');
  const html = await res.text();
  document.getElementById('form-container').innerHTML = html;
});

// Submit form data to /submit
document.getElementById('submit').addEventListener('click', async () => {
  const form = document.querySelector('#form-container form');
  const data = new FormData(form);
  const json = {
    name: data.get('name'),
    career: data.get('career'),
    pets: data.getAll('pets')
  };
  const res = await fetch('/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(json)
  });
  const msg = await res.json();
  document.getElementById('results').textContent = res.ok ? msg.message : msg.detail;
});

// Trigger analysis at /analyse
document.getElementById('analyse').addEventListener('click', async () => {
  const res = await fetch('/analyse');
  const msg = await res.json();
  document.getElementById('results').textContent = res.ok ? msg.message : msg.detail;
});

// Fetch and display input data from /view/input
document.getElementById('view-input').addEventListener('click', async () => {
  const res = await fetch('/view/input');
  const data = await res.json();
  document.getElementById('results').textContent = JSON.stringify(data, null, 2);
});

// Fetch and display profile from /view/profile
document.getElementById('view-profile').addEventListener('click', async () => {
  const res = await fetch('/view/profile');
  const data = await res.json();

  let html = `<p>${data.suitability}</p>`;
  html += `<h3>Recommended Movie: ${data.movie.title} (${data.movie.year})</h3>`;
  html += `<p>${data.movie.plot}</p>`;

  for (const [pet, url] of Object.entries(data.pet_images)) {
    html += `<h4>Your ${pet}:</h4><img src="${url}" style="max-width:300px">`;
  }

  document.getElementById('results').innerHTML = html;
});