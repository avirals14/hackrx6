'use client';
import { useState } from 'react';

export default function QueryComponent({ hasUploadedFiles, onSubmit, loading, disabled }) {
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!hasUploadedFiles) {
      setError('Please upload at least one document before submitting a query.');
      return;
    }
    if (!query.trim()) {
      setError('Please enter a query.');
      return;
    }
    await onSubmit(query); // Call parent handler
  };

  return (
    <section className="w-full max-w-2xl mx-auto mt-8">
      <form onSubmit={handleSubmit} className="flex items-center gap-2 bg-white rounded-lg shadow-sm border border-gray-200 px-4 py-3">
        <input
          type="text"
          className="flex-1 bg-transparent outline-none text-gray-900 placeholder-gray-400 text-base"
          placeholder="e.g. 46-year-old male, knee surgery in Pune, 3-month-old insurance policy"
          value={query}
          onChange={e => setQuery(e.target.value)}
          disabled={loading || disabled}
        />
        <button
          type="submit"
          className="p-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors duration-200 flex items-center justify-center disabled:bg-blue-400"
          disabled={loading || disabled}
          aria-label="Analyze Query"
        >
          {loading ? (
            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : (
            <>Analyze Query</>
          )}
        </button>
      </form>
      {error && <div className="text-red-500 text-sm mt-2">{error}</div>}
    </section>
  );
} 