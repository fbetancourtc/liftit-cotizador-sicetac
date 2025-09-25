module.exports = async function handler(req, res) {
  if (typeof res.status === 'function') {
    res.status(404).json({ error: 'Not Found' });
  } else {
    res.statusCode = 404;
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ error: 'Not Found' }));
  }
};
