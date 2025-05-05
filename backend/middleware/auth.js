const jwt = require('jsonwebtoken');

module.exports = (req, res, next) => {
  try {
    // Get the token from Authorization header
    const authHeader = req.header('Authorization');

    if (!authHeader) {
      return res.status(401).json({ message: 'Authentication failed: No token provided' });
    }

    // Make sure the format is correct
    if (!authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ message: 'Authentication failed: Invalid token format' });
    }

    const token = authHeader.replace('Bearer ', '');

    if (!token) {
      return res.status(401).json({ message: 'Authentication failed: Token is required' });
    }

    // Verify the token
    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      req.user = decoded;
      next();
    } catch (error) {
      console.error('Token verification error:', error.message);
      return res.status(401).json({ message: 'Authentication failed: Invalid token' });
    }
  } catch (error) {
    console.error('Auth middleware error:', error);
    res.status(401).json({ message: 'Authentication failed' });
  }
};