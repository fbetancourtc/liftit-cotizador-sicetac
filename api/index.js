module.exports = async function handler(req, res) {
  res.status(404).json({ error: 'Not Found' });
};
