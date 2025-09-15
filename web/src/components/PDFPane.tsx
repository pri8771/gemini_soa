import React from "react";

export default function PDFPane({url}:{url:string}){
  // Use iframe to render the uploaded PDF directly from /files/:id.pdf
  return (
    <div className="h-[70vh] overflow-hidden rounded-xl border border-slate-200 bg-white">
      <iframe title="PDF" src={`${url}#toolbar=0&view=FitH`} className="h-full w-full" />
    </div>
  );
}
