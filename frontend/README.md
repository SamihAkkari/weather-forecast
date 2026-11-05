# Weather forecast frontend

The development and preview servers bind to `127.0.0.1:5173` and are not exposed
to other devices on the network. During development, the frontend calls the
local API at `127.0.0.1:8001` directly. In production, it uses the same-origin
`/api` path, which must be reverse-proxied to the API service. Set
`VITE_API_URL` to override the API base URL in either environment.

## Run locally

```sh
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. Start the backend separately on
`127.0.0.1:8001` for live weather data.
