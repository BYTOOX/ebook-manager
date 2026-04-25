const http = require('http');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = process.env.PORT || 3000;

const store = {
  progressByBook: new Map(),
  bookmarksByBook: new Map(),
};

const demoKeys = new Map([
  ['demo-user:demo-device', 'demo-secret'],
]);

function parseApiKeys() {
  const env = process.env.SYNC_API_KEYS;
  if (!env) return demoKeys;

  const map = new Map();
  for (const rawEntry of env.split(',')) {
    const entry = rawEntry.trim();
    if (!entry) continue;
    const [userId, deviceId, apiKey] = entry.split(':');
    if (!userId || !deviceId || !apiKey) continue;
    map.set(`${userId}:${deviceId}`, apiKey);
  }

  return map.size > 0 ? map : demoKeys;
}

const apiKeys = parseApiKeys();

function respondJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
  });
  res.end(body);
}

function badRequest(res, message) {
  return respondJson(res, 400, { error: message });
}

function unauthorized(res, message = 'Unauthorized') {
  return respondJson(res, 401, { error: message });
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', chunk => {
      data += chunk;
      if (data.length > 1024 * 1024) {
        reject(new Error('Payload too large'));
      }
    });
    req.on('end', () => {
      if (!data) return resolve({});
      try {
        resolve(JSON.parse(data));
      } catch (err) {
        reject(new Error('Invalid JSON payload'));
      }
    });
    req.on('error', reject);
  });
}

function requireApiKey(req, res) {
  const userId = req.headers['x-user-id'];
  const deviceId = req.headers['x-device-id'];
  const apiKey = req.headers['x-api-key'];

  if (!userId || !deviceId || !apiKey) {
    unauthorized(res, 'Missing x-user-id, x-device-id or x-api-key headers');
    return null;
  }

  const expected = apiKeys.get(`${userId}:${deviceId}`);
  if (!expected || expected !== apiKey) {
    unauthorized(res, 'Invalid API credentials');
    return null;
  }

  return { userId, deviceId };
}

function validateSyncPayload(payload) {
  const { book_id: bookId, device_id: deviceId, cfi, position, updated_at: updatedAt } = payload;

  if (!bookId || typeof bookId !== 'string') return 'book_id is required (string)';
  if (!deviceId || typeof deviceId !== 'string') return 'device_id is required (string)';
  if (typeof cfi !== 'string' && typeof position !== 'number') {
    return 'Either cfi (string) or position (number) is required';
  }
  if (!updatedAt || Number.isNaN(Date.parse(updatedAt))) {
    return 'updated_at is required (ISO date string)';
  }

  return null;
}

function setLastWriteWins(map, bookId, record) {
  const current = map.get(bookId);
  if (!current || Date.parse(record.updated_at) >= Date.parse(current.updated_at)) {
    map.set(bookId, record);
  }
}

function serveStatic(req, res, pathname) {
  const filePath = pathname === '/' ? '/index.html' : pathname;
  const fullPath = path.join(__dirname, 'public', filePath);

  if (!fullPath.startsWith(path.join(__dirname, 'public'))) {
    respondJson(res, 403, { error: 'Forbidden' });
    return;
  }

  fs.readFile(fullPath, (err, content) => {
    if (err) {
      respondJson(res, 404, { error: 'Not found' });
      return;
    }

    const ext = path.extname(fullPath);
    const contentType = {
      '.html': 'text/html; charset=utf-8',
      '.js': 'application/javascript; charset=utf-8',
      '.css': 'text/css; charset=utf-8',
      '.json': 'application/json; charset=utf-8',
    }[ext] || 'text/plain; charset=utf-8';

    res.writeHead(200, { 'Content-Type': contentType });
    res.end(content);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const { pathname } = url;

  if (req.method === 'POST' && pathname === '/sync/progress') {
    const auth = requireApiKey(req, res);
    if (!auth) return;

    try {
      const payload = await parseBody(req);
      const error = validateSyncPayload(payload);
      if (error) return badRequest(res, error);

      if (payload.device_id !== auth.deviceId) {
        return badRequest(res, 'device_id in payload must match x-device-id header');
      }

      const record = {
        type: 'progress',
        book_id: payload.book_id,
        device_id: payload.device_id,
        cfi: payload.cfi ?? null,
        position: payload.position ?? null,
        updated_at: payload.updated_at,
      };

      setLastWriteWins(store.progressByBook, payload.book_id, record);
      return respondJson(res, 200, { ok: true, record });
    } catch (err) {
      return badRequest(res, err.message);
    }
  }

  if (req.method === 'POST' && pathname === '/sync/bookmarks') {
    const auth = requireApiKey(req, res);
    if (!auth) return;

    try {
      const payload = await parseBody(req);
      const error = validateSyncPayload(payload);
      if (error) return badRequest(res, error);

      if (payload.device_id !== auth.deviceId) {
        return badRequest(res, 'device_id in payload must match x-device-id header');
      }

      const record = {
        type: 'bookmark',
        book_id: payload.book_id,
        device_id: payload.device_id,
        cfi: payload.cfi ?? null,
        position: payload.position ?? null,
        updated_at: payload.updated_at,
      };

      setLastWriteWins(store.bookmarksByBook, payload.book_id, record);
      return respondJson(res, 200, { ok: true, record });
    } catch (err) {
      return badRequest(res, err.message);
    }
  }

  const syncBookMatch = pathname.match(/^\/sync\/books\/([^/]+)$/);
  if (req.method === 'GET' && syncBookMatch) {
    const auth = requireApiKey(req, res);
    if (!auth) return;

    const bookId = decodeURIComponent(syncBookMatch[1]);
    const progress = store.progressByBook.get(bookId) || null;
    const bookmark = store.bookmarksByBook.get(bookId) || null;

    const latestRecord = [progress, bookmark]
      .filter(Boolean)
      .sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at))[0] || null;

    return respondJson(res, 200, {
      book_id: bookId,
      progress,
      bookmark,
      latest: latestRecord,
    });
  }

  if (req.method === 'GET') {
    return serveStatic(req, res, pathname);
  }

  respondJson(res, 404, { error: 'Not found' });
});

server.listen(PORT, () => {
  console.log(`ebook-manager listening on http://localhost:${PORT}`);
});
