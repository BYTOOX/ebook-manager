const API_HEADERS = {
  'Content-Type': 'application/json',
  'x-user-id': 'demo-user',
  'x-device-id': 'demo-device',
  'x-api-key': 'demo-secret',
};

const AUTO_SAVE_SECONDS = 10;

const bookIdInput = document.getElementById('book-id');
const positionInput = document.getElementById('position');
const positionValue = document.getElementById('position-value');
const resumeBtn = document.getElementById('resume-btn');
const saveNowBtn = document.getElementById('save-now-btn');
const statusEl = document.getElementById('status');

function setStatus(message) {
  statusEl.textContent = `Statut: ${message}`;
}

function currentPosition() {
  return Number(positionInput.value);
}

function updatePositionUI() {
  positionValue.textContent = `${currentPosition()}%`;
}

async function sendSync(endpoint) {
  const payload = {
    book_id: bookIdInput.value,
    device_id: API_HEADERS['x-device-id'],
    position: currentPosition(),
    cfi: `epubcfi(/6/${currentPosition()})`,
    updated_at: new Date().toISOString(),
  };

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: API_HEADERS,
    body: JSON.stringify(payload),
    keepalive: true,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${response.status}`);
  }

  return response.json();
}

async function saveProgress() {
  try {
    await sendSync('/sync/progress');
    setStatus(`progression synchronisée (${new Date().toLocaleTimeString()})`);
  } catch (err) {
    setStatus(`erreur sync: ${err.message}`);
  }
}

async function saveBookmark() {
  try {
    await sendSync('/sync/bookmarks');
  } catch {
    // silencieux: la progression reste prioritaire en UX.
  }
}

async function resumeFromLatest() {
  try {
    const bookId = encodeURIComponent(bookIdInput.value);
    const response = await fetch(`/sync/books/${bookId}`, { headers: API_HEADERS });
    const data = await response.json();

    const source = data.latest || data.progress || data.bookmark;
    if (!source) {
      setStatus('aucune position disponible pour ce livre');
      return;
    }

    if (typeof source.position === 'number') {
      positionInput.value = String(source.position);
      updatePositionUI();
    }

    setStatus(`reprise depuis ${source.position ?? source.cfi} (maj ${source.updated_at})`);
  } catch (err) {
    setStatus(`échec reprise: ${err.message}`);
  }
}

positionInput.addEventListener('input', updatePositionUI);
resumeBtn.addEventListener('click', resumeFromLatest);
saveNowBtn.addEventListener('click', async () => {
  await saveProgress();
  await saveBookmark();
});

setInterval(saveProgress, AUTO_SAVE_SECONDS * 1000);
window.addEventListener('beforeunload', () => {
  const payload = {
    book_id: bookIdInput.value,
    device_id: API_HEADERS['x-device-id'],
    position: currentPosition(),
    cfi: `epubcfi(/6/${currentPosition()})`,
    updated_at: new Date().toISOString(),
  };

  navigator.sendBeacon(
    '/sync/progress',
    new Blob([JSON.stringify(payload)], { type: 'application/json' })
  );
});

updatePositionUI();
setStatus(`autosave actif toutes les ${AUTO_SAVE_SECONDS}s`);
