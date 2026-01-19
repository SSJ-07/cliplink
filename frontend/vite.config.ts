import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    
    // Only use proxy in local development
    const serverConfig = mode === 'development' ? {
      port: 3000,
      host: '0.0.0.0',
      proxy: {
        '/api': {
          target: 'http://localhost:5001',
          changeOrigin: true,
        }
      }
    } : {
      port: 3000,
      host: '0.0.0.0',
    };
    
    return {
      server: serverConfig,
      plugins: [react()],
      resolve: {
        alias: {
          '@': path.resolve(__dirname, '.'),
        },
        extensions: ['.ts', '.tsx', '.js', '.jsx', '.json']
      }
    };
});
