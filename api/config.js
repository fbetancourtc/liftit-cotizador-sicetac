function resolveSupabaseUrl(url) {
  if (!url || url === 'https://your-project-ref.supabase.co') {
    return '';
  }
  return url;
}

function sendJson(res, statusCode, payload) {
  if (typeof res.status === 'function') {
    res.status(statusCode);
  } else {
    res.statusCode = statusCode;
  }
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify(payload));
}

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') {
    sendJson(res, 405, { error: 'Method Not Allowed' });
    return;
  }

  const supabaseUrl = resolveSupabaseUrl(process.env.SUPABASE_PROJECT_URL);
  const supabaseAnonKey = process.env.SUPABASE_ANON_KEY || '';

  sendJson(res, 200, {
    supabase_url: supabaseUrl,
    supabase_anon_key: supabaseAnonKey
  });
};
