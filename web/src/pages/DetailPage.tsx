import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getPO, deleteLineItem, reprocessPO } from "../api";
import PDFPane from "../components/PDFPane";

function KV({label,value}:{label:string,value:any}){ return <div className="kv"><span className="kv-label">{label}:</span><span>{value||"—"}</span></div>; }

export default function DetailPage(){
  const nav = useNavigate();
  const { id } = useParams();
  const [po,setPo]=useState<any|null>(null);
  const [loading,setLoading]=useState(true);

  async function load(){
    if(!id) return;
    try{
      const d = await getPO(id);
      setPo(d);
    }finally{
      setLoading(false);
    }
  }
  useEffect(()=>{ load(); },[id]);
  useEffect(()=>{
    const t = setInterval(()=>{
      if(po && (po.status==='queued' || po.status==='processing')){ load(); }
    }, 2000);
    return ()=>clearInterval(t);
  },[po]);

  if(loading) return <div className="text-sm text-slate-600">Loading…</div>;
  if(!po) return <div className="text-sm text-slate-600">Not found.</div>;

  return (
    <div className="grid gap-6">
      <div className="flex items-center justify-between">
        <div className="text-xl font-semibold">{po.filename}</div>
        <div className="flex gap-2">
          {po.status==='failed' && <button className="rounded border border-slate-300 px-3 py-1" onClick={()=>reprocessPO(po.id).then(load)}>Reprocess</button>}
          <button className="rounded border border-slate-300 px-3 py-1" onClick={()=>nav("/")}>Back</button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card card-shadow">
          <div className="mb-2 text-sm font-semibold">Buyer</div>
          <KV label="Name" value={po.buyer?.name}/>
          <KV label="Street" value={po.buyer?.street}/>
          <KV label="City" value={po.buyer?.city}/>
          <KV label="Postal" value={po.buyer?.postal}/>
          <div className="mt-4 text-sm font-semibold">Ship To</div>
          <KV label="Name" value={po.ship_to?.name}/>
          <KV label="Street" value={po.ship_to?.street}/>
          <KV label="City" value={po.ship_to?.city}/>
          <KV label="Postal" value={po.ship_to?.postal}/>
          <KV label="Ship To ID" value={po.ship_to?.ship_to_id}/>
        </div>
        <div className="card card-shadow">
          <div className="mb-2 text-sm font-semibold">PO PDF</div>
          <PDFPane url={po.pdf_url} />
        </div>
      </div>

      

      <div className="card card-shadow">
        <div className="mb-2 text-sm font-semibold uppercase tracking-wide">Line Items</div>
        <div className="overflow-hidden rounded-2xl border border-slate-200">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-slate-600">
              <tr><th className="py-2 pl-3">Description</th><th>Qty</th><th>Unit</th><th>Total</th><th>Conf</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {po.line_items?.map((li:any)=>(
                <tr key={li.id} className="border-t border-slate-200">
                  <td className="py-2 pl-3">{li.description}</td>
                  <td>{li.quantity}</td>
                  <td>{li.unit_price}</td>
                  <td>{li.total_price}</td>
                  <td title={`${Math.round((li.confidence||0)*100)}%`} className={(li.confidence||0)>0.8?'text-green-700':(li.confidence||0)>0.5?'text-amber-700':'text-rose-700'}>
                    {Math.round((li.confidence||0)*100)}%
                  </td>
                  <td><button className="rounded border border-slate-300 px-2 py-1" onClick={async()=>{ await deleteLineItem(po.id, li.id); const d=await getPO(po.id); setPo(d); }}>Delete</button></td>
                </tr>
              ))}
              {!po.line_items?.length && <tr><td colSpan={6} className="py-4 text-center text-slate-500">No line items parsed.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>

<div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card card-shadow">
          <div className="mb-2 text-sm font-semibold uppercase tracking-wide">Raw OCR</div>
          <div className="max-h-60 overflow-auto rounded border border-slate-200 bg-white p-3">
            <pre className="whitespace-pre-wrap text-xs">{po.ocr_text || "—"}</pre>
          </div>
        </div>
        <div className="card card-shadow">
          <div className="mb-2 text-sm font-semibold uppercase tracking-wide">Gemini Labeled JSON</div>
          <div className="max-h-60 overflow-auto rounded border border-slate-200 bg-white p-3">
            <pre className="whitespace-pre text-xs">{po.llm_json ? JSON.stringify(po.llm_json,null,2) : "—"}</pre>
          </div>
        </div>
      </div>
    </div>
  );
}
