// @ts-check
import { defineConfig } from 'astro/config'

import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://kerryhatcher.github.io',
  base: '/georgia-elections-report',
  integrations: [react()],

  vite: {
    plugins: [tailwindcss()],
  },
})