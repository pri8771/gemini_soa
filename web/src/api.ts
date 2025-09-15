import axios from "axios";
export const api = axios.create({ baseURL: "" });
api.interceptors.response.use((r)=>r,(err)=>{ const msg = err?.response?.data?.detail || err?.message || "Request failed"; console.error("API error:", msg); alert(msg); return Promise.reject(err); });
export async function getStats(){ const {data}=await api.get("/api/stats"); return data; }
export async function listPOs(){ const {data}=await api.get("/api/po"); return data; }
export async function getPO(id:string){ const {data}=await api.get(`/api/po/${id}`); return data; }
export async function deleteLineItem(poId:string, itemId:string){ await api.delete(`/api/po/${poId}/line-item/${itemId}`); }
export async function reprocessPO(poId:string){ await api.post(`/api/po/${poId}/reprocess`); }
export async function getPrompts(){ const {data}=await api.get("/api/prompts"); return data; }
export async function savePrompts(payload:any){ await api.post("/api/prompts", payload); }
export async function getLogs(tail:number=400){ const {data}=await api.get(`/api/logs?tail=${tail}`); return data; }
export async function uploadPO(file: File){ const form = new FormData(); form.append("file", file); const {data} = await api.post("/api/upload", form); return data; }
