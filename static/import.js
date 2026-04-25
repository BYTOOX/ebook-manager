const sourceTypeEl = document.getElementById('source-type');
const sourcePathEl = document.getElementById('source-path');
const previewBtn = document.getElementById('preview-btn');
const previewMeta = document.getElementById('preview-meta');
const previewOutput = document.getElementById('preview-output');
const importBtn = document.getElementById('import-btn');
const resultOutput = document.getElementById('result-output');
const progressBtn = document.getElementById('progress-btn');
const progressJson = document.getElementById('progress-json');
const progressResult = document.getElementById('progress-result');

const formatJson = (value) => JSON.stringify(value, null, 2);

previewBtn.addEventListener('click', async () => {
  const payload = {
    sourceType: sourceTypeEl.value,
    sourcePath: sourcePathEl.value.trim(),
  };

  const response = await fetch('/api/import/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    previewMeta.textContent = `Erreur: ${data.error}`;
    importBtn.disabled = true;
    return;
  }

  previewMeta.textContent = `${data.total} fichier(s), ${data.duplicates} doublon(s) détecté(s).`;
  previewOutput.textContent = formatJson(data.files);
  importBtn.disabled = false;
});

importBtn.addEventListener('click', async () => {
  const payload = {
    sourceType: sourceTypeEl.value,
    sourcePath: sourcePathEl.value.trim(),
  };

  const response = await fetch('/api/import/commit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  resultOutput.textContent = formatJson(data);
});

progressBtn.addEventListener('click', async () => {
  let payload;
  try {
    payload = JSON.parse(progressJson.value);
  } catch {
    progressResult.textContent = 'JSON invalide.';
    return;
  }

  const response = await fetch('/api/import/progress', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    progressResult.textContent = `Erreur: ${data.error}`;
    return;
  }

  progressResult.textContent = `Progress importée: ${data.imported}/${data.total}.`;
});
