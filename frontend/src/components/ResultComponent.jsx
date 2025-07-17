export default function ResultComponent({ result, loading }) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-8 max-w-2xl mx-auto">
        <svg className="animate-spin h-8 w-8 text-blue-600 mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <div className="text-blue-600 font-medium">Processing…</div>
      </div>
    );
  }
  if (!result) return null;

  // Handle error result
  if (result.error) {
    return (
      <div className="bg-white rounded-lg shadow-lg border border-red-200 p-6 mt-8 max-w-2xl mx-auto">
        <h2 className="text-lg font-semibold text-red-600 mb-4">Error</h2>
        <div className="mb-2 text-red-700">{result.error}</div>
        {result.raw_response && (
          <details className="mt-2">
            <summary className="cursor-pointer text-xs text-gray-500">Show raw backend output</summary>
            <pre className="text-xs text-gray-500 bg-gray-100 p-2 rounded">{result.raw_response}</pre>
          </details>
        )}
        {result.exception && (
          <div className="mt-2 text-xs text-gray-400">Exception: {result.exception}</div>
        )}
      </div>
    );
  }

  // Normal result rendering
  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-6 mt-8 max-w-2xl mx-auto">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Result</h2>
      {result.summary && (
        <div className="mb-4 text-lg font-bold text-blue-700">{result.summary}</div>
      )}
      <div className="mb-2">
        <span className="font-medium">Decision:</span>{" "}
        <span className={result.decision === "approved" ? "text-green-600 font-bold" : "text-red-600 font-bold"}>
          {result.decision}
        </span>
      </div>
      <div className="mb-2">
        <span className="font-medium">Amount:</span>{" "}
        <span>{result.amount !== undefined && result.amount !== null && result.amount !== "" ? result.amount : "N/A"}</span>
      </div>
      {result.justification && (
        <div className="mb-2">
          <span className="font-medium">Justification:</span>
          {Array.isArray(result.justification.clauses) && result.justification.clauses.length > 0 && (
            <ul className="list-disc ml-6 mt-1 text-gray-700">
              {result.justification.clauses.map((clause, idx) => (
                <li key={idx}>
                  <span className="font-mono">{clause.reference ? (
                    <span title={clause.text} className="underline cursor-help">{clause.reference}</span>
                  ) : clause.text}</span>
                </li>
              ))}
            </ul>
          )}
          {result.justification.explanation && (
            <div className="mt-2 text-gray-700">{result.justification.explanation}</div>
          )}
        </div>
      )}
      {/* Fallback for simple string justification */}
      {typeof result.justification === "string" && (
        <div className="mb-2 text-gray-700">{result.justification}</div>
      )}
    </div>
  );
} 