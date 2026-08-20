import path from 'node:path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/torker/',
  build: {
    outDir: path.resolve(__dirname, '../../dist/torker'),
    emptyOutDir: true,
  },
  server: {
    port: 5173,
  },
});
