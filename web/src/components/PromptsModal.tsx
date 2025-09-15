import React, { useEffect, useState } from "react";
import { getPrompts, savePrompts } from "../api";

export default function PromptsModal({open,onClose}:{open:boolean;onClose:()=>void}){
  const [globalPrompt,setGlobalPrompt]=useState("");
  const [customerKey,setCustomerKey]=useState("");
  const [customerPrompt,setCustomerPrompt]=useState("");
  const [saving,setSaving]=useState(false);
  const [loaded,setLoaded]=useState(false);

  useEffect(()=>{
    if(open && !loaded){
      getPrompts().then(data=>{
        setGlobalPrompt(data.global_prompt||"");
        setLoaded(true);
      }).catch(()=>{});
    }
  },[open,loaded]);

  async function saveAll(){
    setSaving(true);
    try{
      await savePrompts({global_prompt:globalPrompt});
      if(customerKey && customerPrompt){
        await savePrompts({customer_key:customerKey, customer_prompt:customerPrompt});
      }
      onClose();
    }finally{
      setSaving(false);
    }
  }

  if(!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-3xl rounded-2xl bg-white p-5 shadow-lg">
        <div className="mb-3 flex items-center justify-between">
          <div className="text-lg font-semibold">Prompt Engineering</div>
          <button onClick={onClose} className="rounded border border-slate-300 px-2 py-1">Close</button>
        </div>
        <div className="grid gap-4">
          <div>
            <div className="mb-1 text-sm font-medium text-slate-700">Global Prompt</div>
            <textarea value={globalPrompt} onChange={e=>setGlobalPrompt(e.target.value)} rows={6} className="w-full rounded border border-slate-300 p-2" placeholder="Instructions that apply to all customers..."/>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-1">
              <div className="mb-1 text-sm font-medium text-slate-700">Customer Key</div>
              <input value={customerKey} onChange={e=>setCustomerKey(e.target.value)} placeholder="e.g., ACME_CORP" className="w-full rounded border border-slate-300 p-2"/>
            </div>
            <div className="col-span-2">
              <div className="mb-1 text-sm font-medium text-slate-700">Customer-specific Prompt</div>
              <textarea value={customerPrompt} onChange={e=>setCustomerPrompt(e.target.value)} rows={4} className="w-full rounded border border-slate-300 p-2" placeholder="Extra instructions for this customer..."/>
            </div>
          </div>
        </div>
        <div className="mt-4 flex justify-end gap-2">
          <button onClick={onClose} className="rounded border border-slate-300 px-3 py-1">Cancel</button>
          <button onClick={saveAll} className="rounded bg-sky-600 px-3 py-1 text-white">{saving?"Saving...":"Save"}</button>
        </div>
      </div>
    </div>
  );
}
