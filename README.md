# weather-forecast

# dev
copy .env.dev .env
docker compose up -d
cd frontend && npm run dev        # http://127.0.0.1:5173

# prod test (same machine)
docker compose down
copy .env.localprod .env
docker compose up -d --build      # starts frontend + caddy as well
# open http://localhost