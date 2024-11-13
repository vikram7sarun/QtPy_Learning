import React, { useState, useCallback } from 'react';
import { AlertCircle, Check, FileCode, Upload } from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';

const API_URL = 'http://localhost:8000';

const CodeReviewApp = () => {
  const [file, setFile] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedAnalyzers, setSelectedAnalyzers] = useState({
    pylint: true,
    flake8: true,
    radon: true,
    bandit: true
  });

  const analyzers = [
    { id: 'pylint', label: 'Pylint' },
    { id: 'flake8', label: 'Flake8' },
    { id: 'radon', label: 'Radon (Complexity)' },
    { id: 'bandit', label: 'Bandit (Security)' }
  ];

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.py')) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a Python (.py) file');
      setFile(null);
    }
  };

  const handleAnalyze = useCallback(async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    const activeAnalyzers = Object.entries(selectedAnalyzers)
      .filter(([_, value]) => value)
      .map(([key]) => key);

    if (activeAnalyzers.length === 0) {
      setError('Please select at least one analyzer');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('analyzers', JSON.stringify(activeAnalyzers));

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Analysis failed');
      }

      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }

      setResults(data);
    } catch (err) {
      setError(err.message || 'Failed to analyze code. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [file, selectedAnalyzers]);

  const ResultSection = ({ results }) => {
    if (!results) return null;

    return (
      <div className="border rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-4">Analysis Results for {results.filename}</h2>
        <div className="space-y-4">
          {Object.entries(results.results).map(([tool, result]) => (
            <div key={tool} className="border-t pt-4">
              <h3 className="font-medium mb-2 capitalize">{tool} Results</h3>
              {result.error ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error in {tool}</AlertTitle>
                  <AlertDescription>{result.error}</AlertDescription>
                </Alert>
              ) : (
                <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm whitespace-pre-wrap">
                  {result.raw || JSON.stringify(result.data, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Code Review Tool</h1>

      <div className="mb-6 p-4 border rounded-lg bg-gray-50">
        <div className="flex items-center gap-4">
          <label className="flex-1">
            <div className="flex items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer hover:bg-gray-100">
              <div className="text-center">
                <FileCode className="mx-auto mb-2" />
                <p className="text-sm">Drop your Python file here or click to browse</p>
                <p className="text-xs text-gray-500 mt-1">{file?.name || 'No file selected'}</p>
              </div>
            </div>
            <input
              type="file"
              accept=".py"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
        </div>
      </div>

      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-3">Select Analyzers</h2>
        <div className="grid grid-cols-2 gap-4">
          {analyzers.map(({ id, label }) => (
            <label key={id} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedAnalyzers[id]}
                onChange={(e) => setSelectedAnalyzers(prev => ({
                  ...prev,
                  [id]: e.target.checked
                }))}
                className="rounded border-gray-300"
              />
              <span>{label}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="flex gap-4 mb-6">
        <button
          onClick={handleAnalyze}
          disabled={!file || loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? (
            <>
              <Upload className="animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Check />
              Run Analysis
            </>
          )}
        </button>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <ResultSection results={results} />
    </div>
  );
};

export default CodeReviewApp;
