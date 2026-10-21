import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({root:'local',plugins:[react()],base:'/assets/',build:{outDir:'../local-dist',emptyOutDir:true,rollupOptions:{output:{entryFileNames:'app.js',chunkFileNames:'chunk-[hash].js',assetFileNames:asset=>asset.name?.endsWith('.css')?'app.css':'[name][extname]'}}}});
