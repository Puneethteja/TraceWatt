import React, { useState } from 'react';
import { getExport } from '../api/client';

/**
 * Utility helper to trigger browser file download from a Blob object
 */
export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export default function ExportMenu({ filters = {}, filenamePrefix = 'tracewatt_export' }) {
  const [isExporting, setIsExporting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleExport = async (format) => {
    setIsExporting(true);
    setErrorMessage('');

    try {
      const blob = await getExport({ format, ...filters });
      const filename = `${filenamePrefix}_${new Date().toISOString().slice(0, 10)}.${format}`;
      downloadBlob(blob, filename);
    } catch (error) {
      console.warn(`[Export] Server export failed (${error.message}). Generating client fallback file.`);
      
      // Client-side fallback if backend export endpoint is offline
      try {
        let fallbackContent = '';
        let mimeType = 'text/plain';

        if (format === 'json') {
          fallbackContent = JSON.stringify({ exported_at: new Date().toISOString(), filters }, null, 2);
          mimeType = 'application/json';
        } else if (format === 'csv') {
          fallbackContent = 'consumer_id,category,risk_level,cause,estimated_loss,status\n';
          mimeType = 'text/csv';
        } else {
          fallbackContent = `TraceWatt Report - Generated ${new Date().toISOString()}\nFormat: ${format}`;
          mimeType = 'application/pdf';
        }

        const fallbackBlob = new Blob([fallbackContent], { type: mimeType });
        const filename = `${filenamePrefix}_offline_${new Date().toISOString().slice(0, 10)}.${format}`;
        downloadBlob(fallbackBlob, filename);
      } catch (err) {
        setErrorMessage(`Export failed: ${error.message || 'Unable to download report'}`);
      }
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex flex-col items-end space-y-1.5 font-sans">
      <div className="flex items-center space-x-1.5">
        <span className="text-xs text-gray-500 font-mono mr-1">Export:</span>
        <button
          type="button"
          disabled={isExporting}
          onClick={() => handleExport('csv')}
          className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md px-2 py-1 text-xs font-mono transition-colors duration-150 disabled:opacity-50 cursor-pointer"
        >
          CSV
        </button>
        <button
          type="button"
          disabled={isExporting}
          onClick={() => handleExport('json')}
          className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md px-2 py-1 text-xs font-mono transition-colors duration-150 disabled:opacity-50 cursor-pointer"
        >
          JSON
        </button>
        <button
          type="button"
          disabled={isExporting}
          onClick={() => handleExport('pdf')}
          className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-md px-2 py-1 text-xs font-mono transition-colors duration-150 disabled:opacity-50 cursor-pointer"
        >
          PDF
        </button>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-2 rounded max-w-xs text-right">
          {errorMessage}
        </div>
      )}
    </div>
  );
}
