import { defineConfig } from '@rsbuild/core';
import { pluginReact } from '@rsbuild/plugin-react';

export default defineConfig(() => {
  return {
    plugins: [pluginReact()],
    source: { entry: { index: './frontend/index' } },
    server: { proxy: { '/v1/web-api': 'http://127.0.0.1:8000' } },
    html: { title: 'Agents Play' },
  };
});
