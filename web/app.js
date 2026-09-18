const form = document.querySelector('#scan-form');
const results = document.querySelector('#results');
const emptyState = document.querySelector('#empty-state');
const resultsList = document.querySelector('#results-list');
const resultCount = document.querySelector('#result-count');
const resultsTitle = document.querySelector('#results-title');
const button = form.querySelector('button');
const staticSourcesUrl = 'sources.json';
const apiUrl = (window.TRACE_API_URL || '').replace(/\/$/, '');

const labels = {
  match: 'Treffer',
  manual_review: 'Prüfung nötig',
  no_match: 'Kein Treffer',
  unavailable: 'Nicht erreichbar'
};

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  }[character]));
}

function resultCard(finding, index) {
  const title = finding.title || finding.source;
  const status = labels[finding.status] || finding.status;
  const excerpt = finding.excerpt || 'Für diese Quelle wurde kein auswertbarer Text gefunden.';
  return `<article class="result-card" style="animation-delay: ${index * 70}ms">
    <span class="result-number">${String(index + 1).padStart(2, '0')}</span>
    <div>
      <h3><a href="${escapeHtml(finding.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a></h3>
      <div class="result-url">${escapeHtml(finding.url)}</div>
      <p class="result-excerpt">${escapeHtml(excerpt)}</p>
    </div>
    <span class="result-status ${escapeHtml(finding.status)}">${escapeHtml(status)}</span>
  </article>`;
}

async function staticFindings(name) {
  const response = await fetch(staticSourcesUrl);
  if (!response.ok) throw new Error('Die statische Quellenliste ist nicht erreichbar.');
  const sources = await response.json();
  return sources.map((source) => ({
    source: source.name,
    url: source.url,
    title: source.name,
    status: 'manual_review',
    excerpt: `Öffne die konfigurierte Quelle und prüfe selbst, ob sie zu ${name} gehört.`,
  }));
}

async function wikipediaFindings(name, birthDate) {
  const params = new URLSearchParams({
    action: 'query',
    list: 'search',
    srsearch: name,
    srnamespace: '0',
    srlimit: '8',
    srprop: 'snippet',
    format: 'json',
    origin: '*'
  });
  const response = await fetch(
    `https://de.wikipedia.org/w/api.php?${params.toString()}`
  );
  if (!response.ok) throw new Error('Die öffentliche Quellenabfrage ist nicht erreichbar.');
  const data = await response.json();
  return (data.query?.search || []).map((item) => ({
    source: 'Wikimedia / Wikipedia',
    url: `https://de.wikipedia.org/wiki/${encodeURIComponent(item.title.replaceAll(' ', '_'))}`,
    title: item.title,
    status: 'manual_review',
    excerpt: `${item.snippet.replace(/<[^>]*>/g, '')} Prüfe den Treffer anhand des Geburtsdatums ${birthDate}.`
  }));
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  button.disabled = true;
  button.querySelector('.button-label').textContent = 'Quellen werden geprüft';
  emptyState.hidden = true;
  results.hidden = false;
  resultsTitle.textContent = 'Suche läuft …';
  resultsList.innerHTML = '<p class="error-message" style="color: var(--muted)">Öffentliche Quellen werden nacheinander geprüft.</p>';
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });

  try {
    let data;
    const isLocalServer = ['localhost', '127.0.0.1'].includes(window.location.hostname);
    if (isLocalServer || apiUrl) {
      const endpoint = apiUrl ? `${apiUrl}/scan` : 'scan';
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(new FormData(form))
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.error || 'Der Suchserver ist nicht erreichbar.');
      }
      data = await response.json();
    } else {
      data = {
        subject: { name: form.name.value },
        findings: await wikipediaFindings(form.name.value, form.birth_date.value)
      };
    }
    const findings = data.findings || [];
    resultsTitle.textContent = `Spuren für ${data.subject.name}`;
    resultCount.textContent = `${findings.length} QUELLE${findings.length === 1 ? '' : 'N'} GEPRÜFT`;
    resultsList.innerHTML = findings.length
      ? findings.map(resultCard).join('')
      : '<p class="error-message">Keine öffentlichen Treffer für diese Namenssuche.</p>';
  } catch (error) {
    resultsTitle.textContent = 'Suche nicht möglich';
    resultCount.textContent = '';
    resultsList.innerHTML = `<p class="error-message">${escapeHtml(error.message)}</p>`;
  } finally {
    button.disabled = false;
    button.querySelector('.button-label').textContent = 'Erneut suchen';
  }
});
