"use client";
import React, { useState } from "react";

export default function SearchPage() {
  const [searchTerm, setSearchTerm] = useState("");
  // Update the initial state to be more specific about the type of data expected
  const [searchResults, setSearchResults] = useState<Array<{id: string, content: string, similarity_score: number, reranking_score?: number, voice?: number, curations_count?: number, created_at: string}>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (event: React.FormEvent) => {
    event.preventDefault(); // Prevent the form from refreshing the page
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
      setSearchResults(data); // Assuming the response is now correctly typed
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
    <div>
      <h1>Search</h1>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Enter search term"
        />
        <button type="submit" disabled={isLoading}>
          Search
        </button>
      </form>

      {isLoading && <p>Loading...</p>}
      {error && <p>Error: {error}</p>}

      <div>
        {searchResults.length > 0 && (
          <ul>
            {searchResults.map((result) => (
              <li key={result.id}>
                <p>Content: {result.content}</p>
                <p>Similarity Score: {result.similarity_score}</p>
                {/* Render other properties as needed */}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
