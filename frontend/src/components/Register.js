import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';
import BotLogo from '../assets/bot-logo.png';
import AnimatedBackground from './AnimatedBackground';

const Register = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      return setError('Passwords do not match');
    }

    try {
      setError('');
      setLoading(true);
      const success = await register(username, email, password);
      if (success) {
        navigate('/');
      } else {
        setError('Failed to create an account.');
      }
    } catch (err) {
      setError('An error occurred during registration.');
    }
    setLoading(false);
  };

  return (
    <AnimatedBackground>
      <Container component="main" maxWidth="xs">
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
            <img
              src={BotLogo}
              alt="Zentra Logo"
              style={{
                width: 100,
                height: 100,
                borderRadius: '50%',
                padding: 8,
                background: 'rgba(255, 255, 255, 0.95)',
                border: '1px solid rgba(90, 107, 255, 0.25)',
                boxShadow: '0 0 25px rgba(90, 107, 255, 0.6)'
              }}
            />
          </Box>
          <Paper elevation={6} sx={{
            p: 4,
            width: '100%',
            backgroundColor: 'rgba(30, 33, 58, 0.95)',
            backdropFilter: 'blur(10px)',
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
          }}>
            <Typography
              component="h1"
              variant="h5"
              align="center"
              gutterBottom
              sx={{
                fontWeight: 600,
                color: '#fff',
                mb: 2
              }}
            >
              Create an Account
            </Typography>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            <form onSubmit={handleSubmit}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="Username"
                name="username"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    color: '#fff',
                    '& fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.3)',
                    },
                    '&:hover fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.5)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: 'rgba(90, 107, 255, 0.8)',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: 'rgba(255, 255, 255, 0.7)',
                  },
                  mb: 1.5
                }}
                InputLabelProps={{
                  style: { color: 'rgba(255, 255, 255, 0.7)' },
                }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label="Email Address"
                name="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    color: '#fff',
                    '& fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.3)',
                    },
                    '&:hover fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.5)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: 'rgba(90, 107, 255, 0.8)',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: 'rgba(255, 255, 255, 0.7)',
                  },
                  mb: 1.5
                }}
                InputLabelProps={{
                  style: { color: 'rgba(255, 255, 255, 0.7)' },
                }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    color: '#fff',
                    '& fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.3)',
                    },
                    '&:hover fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.5)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: 'rgba(90, 107, 255, 0.8)',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: 'rgba(255, 255, 255, 0.7)',
                  },
                  mb: 1.5
                }}
                InputLabelProps={{
                  style: { color: 'rgba(255, 255, 255, 0.7)' },
                }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                name="confirmPassword"
                label="Confirm Password"
                type="password"
                id="confirmPassword"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    color: '#fff',
                    '& fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.3)',
                    },
                    '&:hover fieldset': {
                      borderColor: 'rgba(255, 255, 255, 0.5)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: 'rgba(90, 107, 255, 0.8)',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: 'rgba(255, 255, 255, 0.7)',
                  },
                  mb: 1
                }}
                InputLabelProps={{
                  style: { color: 'rgba(255, 255, 255, 0.7)' },
                }}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{
                  mt: 3,
                  mb: 2,
                  py: 1.2,
                  background: 'linear-gradient(90deg, rgba(90,107,255,1) 0%, rgba(113,88,245,1) 100%)',
                  '&:hover': {
                    background: 'linear-gradient(90deg, rgba(113,88,245,1) 0%, rgba(90,107,255,1) 100%)',
                    boxShadow: '0 4px 15px rgba(90, 107, 255, 0.4)',
                  },
                  fontSize: '1rem',
                  fontWeight: 500,
                  textTransform: 'none'
                }}
                disabled={loading}
              >
                {loading ? 'Creating Account...' : 'Sign Up'}
              </Button>
              <Box sx={{ textAlign: 'center' }}>
                <Link to="/login" style={{ textDecoration: 'none' }}>
                  <Typography variant="body2" sx={{ color: '#5A6BFF', fontWeight: 500 }}>
                    Already have an account? Sign in
                  </Typography>
                </Link>
              </Box>
            </form>
          </Paper>
        </Box>
      </Container>
    </AnimatedBackground>
  );
};

export default Register;