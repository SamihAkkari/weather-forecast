import tailwindcss from "@tailwindcss/vite";
import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import { nitro } from "nitro/vite";

const localServer = {
  host: "127.0.0.1",
  port: 5173,
  strictPort: true,
  proxy: {
    "/api": {
      target: "http://127.0.0.1:8001",
      changeOrigin: true,
      rewrite: (path: string) => path.replace(/^\/api/, ""),
    },
  },
};

export default defineConfig({
  plugins: [
    ...tanstackStart({
      server: { entry: "server" },
    }),
    react(),
    tailwindcss(),
    nitro(),
  ],
  resolve: { tsconfigPaths: true },
  server: localServer,
  preview: localServer,
});
