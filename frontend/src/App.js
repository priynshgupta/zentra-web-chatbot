import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Login from './components/Login';
import Register from './components/Register';
import Chat from './components/Chat';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AppBar, Toolbar, Typography, Button, Container } from '@mui/material';
import WebsiteCategorizer from './components/WebsiteCategorizer';
import WebsiteList from './components/WebsiteList';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#181A20',
      paper: '#23262F'
    },
    primary: {
      main: '#3B82F6'
    },
    secondary: {
      main: '#6366F1'
    }
  },
  typography: {
    fontFamily: 'Inter, Roboto, Arial, sans-serif'
  }
});

const PrivateRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <AuthProvider>
        <Router basename={process.env.PUBLIC_URL}>
          <Container>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route
                path="/"
                element={
                  <PrivateRoute>
                    <Chat />
                  </PrivateRoute>
                }
              />
              <Route path="/websites" element={<WebsiteList />} />
            </Routes>
          </Container>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;