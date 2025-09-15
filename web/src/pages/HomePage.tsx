import React, { useEffect, useMemo, useRef, useState } from "react";
import { getStats, listPOs, uploadPO, getLogs, reprocessPO } from "../api";
import { useNavigate } from "react-router-dom";

type PO = any;
function useInterval(cb: ()=>void, ms: number){ React.useEffect(()=>{ const id=setInterval(cb, ms); return ()=>clearInterval(id); },[cb,ms]); }
function StatusBadge({s}:{s:string}){
  const v = (s||"").toLowerCase();
  const cls = v==="processing"?"badge-processing":v==="complete"?"badge-complete":v==="failed"?"badge-failed":"badge-queued";
  return <span className={`badge ${cls}`}>{s}</span>;
}
function Progress({v}:{v:number}){ return <div className="progress"><div style={{width:`${Math.min(100, Math.max(0,v))}%`}}/></div>; }
function Stat({label, value}:{label:string,value:any}){ return <div className="rounded-xl border border-slate-200 bg-white p-4"><div className="text-xs uppercase text-slate-500">{label}</div><div className="text-lg font-semibold">{value}</div></div>; }

export default function HomePage(){
  const nav = useNavigate();
  const [pos,setPos]=useState<PO[]>([]);
  const [stats,setStats]=useState<any>({});
  const [uploading,setUploading]=useState(false);
  const [backendUp,setBackendUp]=useState(true);
  const [logs,setLogs]=useState<string[]>([]);
  const [paused,setPaused]=useState(false);
  const [filter,setFilter]=useState("");
  const fileInputRef = useRef<HTMLInputElement|null>(null);

  async function refreshList(){
    const [s, list] = await Promise.all([getStats(), listPOs()]);
    setStats(s); setPos(list);
  }
  useEffect(()=>{ refreshList(); },[]);
  useEffect(()=>{ fetch('/api/health').then(r=>r.ok?setBackendUp(true):setBackendUp(false)).catch(()=>setBackendUp(false)); },[]);
  useInterval(()=>{ if(pos.some(p=>['queued','processing'].includes(String(p.status).toLowerCase()))) refreshList(); }, 1800);
  useInterval(()=>{ if(!paused){ getLogs(500).then(d=>setLogs(d.lines||[])).catch(()=>{}); } }, 1500);
  const filteredLogs = useMemo(()=>{ if(!filter) return logs; const k=filter.toLowerCase(); return logs.filter(l=>l.toLowerCase().includes(k)); },[logs,filter]);
  function level(line:string){ if(line.includes(" ERROR ")) return "text-rose-700"; if(line.includes(" WARN")||line.includes(" WARNING ")) return "text-amber-700"; return "text-slate-800"; }

  return (
    <>
      {!backendUp && (
        <div className="mb-4 rounded-xl border border-amber-300 bg-amber-50 px-4 py-2 text-sm text-amber-800">
          Backend is not reachable. Check Docker is running and then refresh.
        </div>
      )}

      <div className="grid gap-6">
        <div className="card card-shadow">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <Stat label="Total" value={stats.total || 0} />
            <Stat label="Completed" value={stats.complete || 0} />
            <Stat label="Processing" value={stats.processing || 0} />
            <Stat label="Failed" value={stats.failed || 0} />
            <Stat label="Avg Confidence" value={(stats.avg_confidence||0).toFixed(2)} />
          </div>
        </div>

        <div className="card card-shadow">
          <div className="mb-3 text-sm font-semibold">Purchase Orders</div>
          <div className="overflow-hidden rounded-2xl border border-slate-200">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr><th className="py-2 pl-3">Created</th><th>Filename</th><th>Status</th><th>Progress</th><th>Actions</th></tr>
              </thead>
              <tbody>
                {pos.map((p:PO)=>(
                  <tr key={p.id} className="border-t border-slate-200">
                    <td className="py-2 pl-3">{new Date(p.created_at).toLocaleString()}</td>
                    <td>{p.filename}</td>
                    <td><StatusBadge s={p.status}/></td>
                    <td><Progress v={p.progress||0}/></td>
                    <td className="flex gap-2 py-2">
                      <button className="rounded bg-sky-600 px-2 py-1 text-white" onClick={()=>nav(`/po/${p.id}`)}>Open</button>
                      {p.status==='failed' && <button className="rounded border border-slate-300 px-2 py-1" onClick={()=>reprocessPO(p.id).then(refreshList)}>Reprocess</button>}
                    </td>
                  </tr>
                ))}
                {!pos.length && <tr><td colSpan={5} className="py-6 text-center text-slate-500">No POs yet.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card card-shadow">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-sm font-semibold">Live Processing Logs</div>
            <div className="flex items-center gap-2">
              <input className="w-64 rounded border border-slate-300 px-2 py-1 text-sm" placeholder="Filter (e.g., po_id, ERROR)" value={filter} onChange={e=>setFilter(e.target.value)}/>
              <button className="rounded border border-slate-300 px-2 py-1 text-sm" onClick={()=>setPaused(p=>!p)}>{paused?'Resume':'Pause'}</button>
            </div>
          </div>
          <div className="h-64 overflow-auto rounded border border-slate-200 bg-white p-3">
            {filteredLogs.length? filteredLogs.map((l,i)=><div key={i} className={`font-mono text-xs leading-5 ${level(l)}`}>{l}</div>): <div className="text-sm text-slate-500">No log lines yet.</div>}
          </div>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={async(e)=>{
          const file=e.target.files?.[0]; if(!file) return;
          try{
            (window as any).__uploading = true;
            await uploadPO(file);
            await refreshList();
          }catch(err:any){
            alert(err?.response?.data?.detail || err?.message || 'Upload failed');
          }finally{
            (window as any).__uploading = false;
            if(fileInputRef.current) fileInputRef.current.value='';
          }
        }}
      />

      <div className="fixed bottom-6 right-6 flex gap-2">
        <button
          className="rounded-full bg-sky-600 px-4 py-2 text-white shadow-md hover:bg-sky-700"
          onClick={()=>fileInputRef.current?.click()}
        >
          { (window as any).__uploading ? "Uploading…" : "Upload PO" }
        </button>
      </div>
    </>
  );
}