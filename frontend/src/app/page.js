"use client";
import { useState } from "react";
import UploadComponent from "../components/UploadComponent";
import QueryComponent from "../components/QueryComponent";
import ResultComponent from "../components/ResultComponent";
import Header from "../components/Header";
import Footer from "../components/Footer";

export default function Home() {
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState("");
  const [lastQuery, setLastQuery] = useState("");

  const handleUploadSuccess = (count) => {
    setToast(`${count} file${count > 1 ? "s" : ""} uploaded and parsed successfully`);
    setTimeout(() => setToast(""), 3000);
  };

  const handleQuerySubmit = async (query) => {
    setLoading(true);
    setResult(null);
    setLastQuery(query);
    try {
      const res = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      if (res.ok) {
        setResult(data.llm_response || data);
      } else {
        setResult({ decision: 'error', amount: '', justification: data.error || 'Unknown error' });
      }
    } catch (err) {
      setResult({ decision: 'error', amount: '', justification: err.message });
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 transition-colors duration-200">
      <Header />
      {toast && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-green-600 text-white px-4 py-2 rounded shadow z-50">
          {toast}
        </div>
      )}
      <main className="container mx-auto px-4 py-8 max-w-6xl flex-1">
        <div className="space-y-8 max-w-2xl mx-auto">
          <UploadComponent
            uploadedFiles={uploadedFiles}
            setUploadedFiles={setUploadedFiles}
            onUploadSuccess={handleUploadSuccess}
          />
          <QueryComponent
            hasUploadedFiles={uploadedFiles.length > 0}
            onSubmit={handleQuerySubmit}
            loading={loading}
            disabled={uploadedFiles.length === 0}
          />
          {/* Show last query and parsed query */}
          {lastQuery && (
            <div className="mb-4 bg-white rounded shadow p-4 border border-gray-100">
              <span className="font-medium">Query:</span> <span className="text-gray-700">"{lastQuery}"</span>
              {result?.structured_query && (
                <div className="mt-2 text-xs text-gray-500">
                  <span className="font-medium">Parsed:</span> {JSON.stringify(result.structured_query)}
                </div>
              )}
            </div>
          )}
          {/* Skeleton loader for result */}
          {loading && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-8 max-w-2xl mx-auto animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
              <div className="h-4 bg-gray-100 rounded w-1/2 mb-2"></div>
              <div className="h-4 bg-gray-100 rounded w-1/4 mb-2"></div>
              <div className="h-4 bg-gray-100 rounded w-2/3 mb-2"></div>
              <div className="h-4 bg-gray-100 rounded w-1/3"></div>
            </div>
          )}
          <ResultComponent result={result} loading={loading} />
        </div>
      </main>
      <Footer />
    </div>
  );
}
