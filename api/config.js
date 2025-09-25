function resolveSupabaseUrl(url) {
  if (!url || url === 'https://your-project-ref.supabase.co') {
    return '';
  }
  return url;
}

module.exports = async function handler(req, res) {
  if (req.method !== 'GET') {
    res.status(405).json({ error: 'Method Not Allowed' });
    return;
  }

  const supabaseUrl = resolveSupabaseUrl(process.env.SUPABASE_PROJECT_URL);
  const supabaseAnonKey = process.env.SUPABASE_ANON_KEY || '';

  res.status(200).json({
    supabase_url: supabaseUrl,
    supabase_anon_key: supabaseAnonKey
  });
};
