import React, { useEffect, useState } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import HomePage from "./pages/HomePage";
import DetailPage from "./pages/DetailPage";
import PromptsModal from "./components/PromptsModal";

const styles = {
  default: { name: "Default", className: "theme-default" },
  glass: { name: "Glassmorphism", className: "theme-glass" },
  neumorph: { name: "Neumorphic", className: "theme-neumorph" },
  enterprise: { name: "Enterprise", className: "theme-enterprise" },
  playful: { name: "Playful", className: "theme-playful" },
  dark: { name: "Dark", className: "theme-dark" },
};

export default function App(){
  const [styleKey,setStyleKey]=useState<keyof typeof styles>(()=> (localStorage.getItem("styleKey") as any) || "default");
  const [promptsOpen,setPromptsOpen]=useState(false);
  useEffect(()=>{ localStorage.setItem("styleKey", String(styleKey)); },[styleKey]);
  const styleCls = styles[styleKey]?.className || styles.default.className;
  const location = useLocation();

  return (
    <div className={`${styleCls}`}>
      <header className="border-b bg-white/70 backdrop-blur">
        <div className="container flex flex-wrap items-center justify-between gap-3 p-4">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-xl font-semibold">PO Extractor — Gemini SOA</Link>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">v5</span>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 rounded-2xl border border-slate-300 bg-white/70 px-3 py-1">
              <span className="text-sm text-slate-600">Style</span>
              <select className="rounded px-2 py-1 text-sm" value={String(styleKey)} onChange={e=>setStyleKey(e.target.value as any)}>
                {Object.entries(styles).map(([k,v])=> <option key={k} value={k}>{v.name}</option>)}
              </select>
            </div>
            <button className="rounded-2xl border border-slate-300 bg-white/70 px-3 py-1 text-sm" onClick={()=>setPromptsOpen(true)}>Prompts</button>
          </div>
        </div>
      </header>

      <main className="container p-6">
        <Routes>
          <Route path="/" element={<HomePage/>} />
          <Route path="/po/:id" element={<DetailPage/>} />
        </Routes>
      </main>

      <PromptsModal open={promptsOpen} onClose={()=>setPromptsOpen(false)}/>
    </div>
  );
}
