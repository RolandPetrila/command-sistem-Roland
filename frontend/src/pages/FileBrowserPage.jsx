import React, { useState } from 'react';
import FileBrowser from '../components/FileBrowser/FileBrowser';
import FilePreview from '../components/FileBrowser/FilePreview';

export default function FileBrowserPage() {
  const [selectedFile, setSelectedFile] = useState('');

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-180px)]">
      <FileBrowser onSelectFile={setSelectedFile} selectedPath={selectedFile} />
      <FilePreview filePath={selectedFile} />
    </div>
  );
}
