import axios from "axios";

const baseURL =
  import.meta.env.VITE_API_URL ??
  (import.meta.env.DEV ? "http://127.0.0.1:8001" : "/api");

const api = axios.create({ baseURL });

export default api;
