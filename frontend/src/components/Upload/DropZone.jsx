import React from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileUp } from 'lucide-react';

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
};

export default function DropZone({ onFilesAdded, disabled = false }) {
  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    accept: ACCEPTED_TYPES,
    disabled,
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0 && onFilesAdded) {
        onFilesAdded(acceptedFiles);
      }
    },
  });

  return (
    <div
      {...getRootProps()}
      className={`relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer
        transition-all duration-300 group ${
          disabled
            ? 'border-slate-700 bg-slate-900/40 cursor-not-allowed opacity-50'
            : isDragReject
            ? 'border-red-500/60 bg-red-500/5'
            : isDragActive
            ? 'border-primary-400 bg-primary-500/10 scale-[1.01]'
            : 'border-slate-700 bg-slate-900/40 hover:border-primary-500/50 hover:bg-slate-900/60'
        }`}
    >
      <input {...getInputProps()} />

      <div className="flex flex-col items-center gap-4">
        <div
          className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-300 ${
            isDragActive
              ? 'bg-primary-500/20 scale-110'
              : 'bg-slate-800 group-hover:bg-primary-600/20'
          }`}
        >
          {isDragActive ? (
            <FileUp className="w-8 h-8 text-primary-400 animate-bounce" />
          ) : (
            <Upload className="w-8 h-8 text-slate-400 group-hover:text-primary-400 transition-colors" />
          )}
        </div>

        <div>
          <p className="text-base font-medium text-slate-200 mb-1">
            {isDragActive
              ? 'Eliberează pentru a adăuga fișierele'
              : isDragReject
              ? 'Tip de fișier neacceptat'
              : 'Trage fișierele aici sau click pentru selectare'}
          </p>
          <p className="text-sm text-slate-400">
            Acceptă fișiere <span className="badge-pdf mx-1">PDF</span> și{' '}
            <span className="badge-docx mx-1">DOCX</span>
          </p>
        </div>
      </div>
    </div>
  );
}
