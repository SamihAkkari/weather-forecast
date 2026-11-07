# weather-forecast

# dev
copy .env.dev .env
docker compose --profile monitoring up -d
cd frontend && npm run dev        # http://127.0.0.1:5173

# prod test (same machine)
docker compose down
copy .env.localprod .env
docker compose --profile monitoring up -d --build # starts frontend + caddy and local monitoring
# open http://localhost