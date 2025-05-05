import React from 'react';
import { Box } from '@mui/material';

const AnimatedBackground = ({ children }) => {
  return (
    <Box
      sx={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        width: '100vw',
        height: '100vh',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #1a1a3a 0%, #0a1128 100%)',
      }}
    >
      {/* Animated circles */}
      {[...Array(8)].map((_, i) => (
        <Box
          key={i}
          sx={{
            position: 'absolute',
            background: 'rgba(90, 107, 255, 0.07)',
            borderRadius: '50%',
            animation: `float ${Math.random() * 8 + 10}s infinite ease-in-out`,
            zIndex: 0,
            '@keyframes float': {
              '0%': {
                transform: 'translateY(0) translateX(0)',
                opacity: Math.random() * 0.15 + 0.05,
              },
              '50%': {
                transform: `translateY(${Math.random() * 60 - 30}px) translateX(${Math.random() * 60 - 30}px)`,
                opacity: Math.random() * 0.2 + 0.1,
              },
              '100%': {
                transform: 'translateY(0) translateX(0)',
                opacity: Math.random() * 0.15 + 0.05,
              },
            },
            width: `${Math.random() * 200 + 100}px`,
            height: `${Math.random() * 200 + 100}px`,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
        />
      ))}

      {/* Network grid background */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          zIndex: 0,
          backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100%25' height='100%25' viewBox='0 0 800 800'%3E%3Cg fill='none' stroke='%236979E8' stroke-width='1'%3E%3Cpath d='M769 229L1037 260.9M927 880L731 737 520 660 309 538 40 599 295 764 126.5 879.5 40 599-197 493 102 382-31 229 126.5 79.5-69-63'/%3E%3Cpath d='M-31 229L237 261 390 382 603 493 308.5 537.5 101.5 381.5M370 905L295 764'/%3E%3Cpath d='M520 660L578 842 731 737 840 599 603 493 520 660 295 764 309 538 390 382 539 269 769 229 577.5 41.5 370 105 295 -36 126.5 79.5 237 261 102 382 40 599 -69 737 127 880'/%3E%3Cpath d='M520-140L578.5 42.5 731-63M603 493L539 269 237 261 370 105M902 382L539 269M390 382L102 382'/%3E%3Cpath d='M-222 42L126.5 79.5 370 105 539 269 577.5 41.5 927 80 769 229 902 382 603 493 731 737M295-36L577.5 41.5M578 842L295 764M40-201L127 80M102 382L-261 269'/%3E%3C/g%3E%3Cg fill='%235A6BFF'%3E%3Ccircle cx='769' cy='229' r='5'/%3E%3Ccircle cx='539' cy='269' r='5'/%3E%3Ccircle cx='603' cy='493' r='5'/%3E%3Ccircle cx='731' cy='737' r='5'/%3E%3Ccircle cx='520' cy='660' r='5'/%3E%3Ccircle cx='309' cy='538' r='5'/%3E%3Ccircle cx='295' cy='764' r='5'/%3E%3Ccircle cx='40' cy='599' r='5'/%3E%3Ccircle cx='102' cy='382' r='5'/%3E%3Ccircle cx='127' cy='80' r='5'/%3E%3Ccircle cx='370' cy='105' r='5'/%3E%3Ccircle cx='578' cy='42' r='5'/%3E%3Ccircle cx='237' cy='261' r='5'/%3E%3Ccircle cx='390' cy='382' r='5'/%3E%3C/g%3E%3C/svg%3E")`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          opacity: 0.1,
          animation: 'animatedBackground 80s linear infinite',
          '@keyframes animatedBackground': {
            '0%': {
              backgroundPosition: '0% 0%',
            },
            '50%': {
              backgroundPosition: '100% 100%',
            },
            '100%': {
              backgroundPosition: '0% 0%',
            },
          },
        }}
      />

      {/* Glow effects */}
      <Box
        sx={{
          position: 'absolute',
          top: '30%',
          left: '15%',
          width: '300px',
          height: '300px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(90,107,255,0.15) 0%, rgba(90,107,255,0) 70%)',
          animation: 'pulse 12s infinite',
          '@keyframes pulse': {
            '0%': { opacity: 0.3, transform: 'scale(1)' },
            '50%': { opacity: 0.6, transform: 'scale(1.1)' },
            '100%': { opacity: 0.3, transform: 'scale(1)' },
          },
          zIndex: 0,
        }}
      />

      <Box
        sx={{
          position: 'absolute',
          bottom: '20%',
          right: '15%',
          width: '350px',
          height: '350px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(90,107,255,0.1) 0%, rgba(90,107,255,0) 70%)',
          animation: 'pulse 16s infinite',
          animationDelay: '2s',
          zIndex: 0,
        }}
      />

      {/* Smaller accent glows */}
      <Box
        sx={{
          position: 'absolute',
          top: '60%',
          right: '25%',
          width: '120px',
          height: '120px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(135,206,250,0.15) 0%, rgba(135,206,250,0) 70%)',
          animation: 'pulse 8s infinite',
          animationDelay: '3s',
          zIndex: 0,
        }}
      />

      <Box
        sx={{
          position: 'absolute',
          top: '20%',
          right: '30%',
          width: '80px',
          height: '80px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 70%)',
          animation: 'pulse 6s infinite',
          animationDelay: '1s',
          zIndex: 0,
        }}
      />

      {/* Content */}
      <Box sx={{ zIndex: 1, width: '100%' }}>
        {children}
      </Box>
    </Box>
  );
};

export default AnimatedBackground;