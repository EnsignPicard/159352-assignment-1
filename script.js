// Load form fragment once the DOM content is loaded
document.addEventListener('DOMContentLoaded', async () => {
  const response = await fetch('/form');
  const html = await response.text();
  document.getElementById('form-container').innerHTML = html;
});

// Submit form data to /submit
document.getElementById('submit').addEventListener('click', async () => {
  const form = document.querySelector('#form-container form');
  const formData = new FormData(form);
  const json = {
    name: formData.get('name'),
    career: formData.get('career'),
    pets: formData.getAll('pets')
  };
  const response = await fetch('/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(json)
  });
  const responseMessage = await response.json();
  if (response.ok) {
    document.getElementById('results').textContent = responseMessage.message;
  } else {
    document.getElementById('results').textContent = responseMessage.detail;
  }
});

// Trigger analysis at /analyse
document.getElementById('analyse').addEventListener('click', async () => {
  const response = await fetch('/analyse');
  const responseMessage = await response.json();
  if (response.ok) {
    document.getElementById('results').textContent = responseMessage.message;
  } else {
    document.getElementById('results').textContent = responseMessage.detail;
  }
});

// Fetch and display input data from /view/input
document.getElementById('view-input').addEventListener('click', async () => {
  const response = await fetch('/view/input');
  const inputData = await response.json();
  document.getElementById('results').textContent = JSON.stringify(inputData, null, 2);
});

// Fetch and display profile from /view/profile
document.getElementById('view-profile').addEventListener('click', async () => {
  const response = await fetch('/view/profile');
  const profileData = await response.json();

  let html = '<p>' + profileData.suitability + '</p>';
  html += '<h3>Recommended Movie: ' + profileData.movie.title + ' (' + profileData.movie.year + ')</h3>';
  html += '<p>' + profileData.movie.plot + '</p>';

  const pets = Object.keys(profileData.pet_images);
  for (let i = 0; i < pets.length; i++) {
    const petName = pets[i];
    const imageUrl = profileData.pet_images[petName];
    html += '<h4>Your ' + petName + ':</h4><img src="' + imageUrl + '" style="max-width:300px">';
  }

  document.getElementById('results').innerHTML = html;
});