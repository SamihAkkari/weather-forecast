# Weather forecast frontend

The development and preview servers bind to `127.0.0.1:5173` and are not exposed
to other devices on the network. The frontend uses the local API at
`127.0.0.1:8001`.

## Run locally

```sh
npm install
npm run dev
```

Open <http://127.0.0.1:5173>. Start the backend separately on
`127.0.0.1:8001` for live weather data.
