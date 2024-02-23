"use client";
import React, { useState } from "react";

export default function SearchPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<
    Array<{
      id: string;
      content: string;
      similarity_score: number;
      reranking_score?: number;
      voice?: number;
      revisions_count?: number;
      created_at?: string;
    }>
  >([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const response = await fetch("/api/resonance_search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ input_text: searchTerm }),
      });

      if (!response.ok) {
        throw new Error("Search failed");
      }

      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      if (error instanceof Error) {
        setError(error.message);
      } else {
        setError("An unexpected error occurred");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-black text-white min-h-screen flex flex-col items-center py-8">
      <h1 className="text-4xl font-bold mb-4">Search</h1>
      <form onSubmit={handleSearch} className="w-full max-w-lg">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Enter search term"
          className="w-full p-4 text-lg bg-gray-800 text-white placeholder-gray-400 border-0 rounded-md focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="mt-4 w-full bg-blue-500 text-white p-4 rounded-md hover:bg-blue-600 disabled:bg-blue-400"
        >
          Search
        </button>
      </form>

      {isLoading && <p>Loading...</p>}
      {error && <p>Error: {error}</p>}

      <div className="w-full max-w-3xl mt-8">
        {searchResults.length > 0 && (
          <ul>
            {searchResults.map((result) => (
              <li
                key={result.id}
                className="mb-4 p-4 bg-gray-800 bg-opacity-80 rounded-lg"
              >
                {result.voice && (
                  <p className="text-lg font-semibold text-blue-400">
                    Voice: {result.voice}
                  </p>
                )}
                <p>ID: {result.id}</p>
                <p className="text-xl font-bold">Content: {result.content}</p>
                <p>Similarity Score: {result.similarity_score}</p>
                {result.reranking_score && (
                  <p>Reranking Score: {result.reranking_score}</p>
                )}
                {result.revisions_count && (
                  <p>Revisions Count: {result.revisions_count}</p>
                )}
                {result.created_at && <p>Created At: {result.created_at}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
