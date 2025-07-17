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

  const handleUploadSuccess = (count) => {
    setToast(`${count} file${count > 1 ? "s" : ""} uploaded and parsed successfully`);
    setTimeout(() => setToast(""), 3000);
  };

  const handleQuerySubmit = async (query) => {
    setLoading(true);
    setResult(null);
    // Simulate backend call
    setTimeout(() => {
      setResult({
        decision: "approved",
        amount: "₹50,000",
        justification: {
          clauses: [
            {
              text: "Section 4.2.1: Knee surgeries are covered after 3 months of policy inception.",
              reference: "policy.pdf - Page 12"
            }
          ],
          explanation: "Policy duration and procedure match requirements."
        }
      });
      setLoading(false);
    }, 2000);
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
        <div className="space-y-8">
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
          <ResultComponent result={result} loading={loading} />
        </div>
      </main>
      <Footer />
    </div>
  );
}
