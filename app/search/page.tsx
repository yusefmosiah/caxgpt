"use client";
import React, { useState } from "react";
import MessageList from "@/components/message-list";

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
  const [sortOrder, setSortOrder] = useState<string>("");

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
  const sortResults = (a, b) => {
    switch (sortOrder) {
      case "voice":
        return (b.voice || 0) - (a.voice || 0);
      case "similarity_score":
        return b.similarity_score - a.similarity_score;
      case "reranking_score":
        return (b.reranking_score || 0) - (a.reranking_score || 0);
      case "revisions_count":
        return (b.revisions_count || 0) - (a.revisions_count || 0);
      case "created_at":
        return (
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
      default:
        return 0;
    }
  };
  return (
    <div className="bg-black text-white min-h-screen flex flex-col items-center py-8">
      <h1 className="text-4xl font-bold mb-4">Search</h1>
      <form onSubmit={handleSearch} className="w-full max-w-lg">
        <select
          value={sortOrder}
          onChange={(e) => setSortOrder(e.target.value)}
          className="mb-4 w-full p-2 bg-gray-800 text-white"
        >
          <option value="">Select Sort Order</option>
          <option value="voice">Voice</option>
          <option value="similarity_score">Similarity Score</option>
          <option value="reranking_score">Reranking Score</option>
          <option value="revisions_count">Revisions Count</option>
          <option value="created_at">Created At</option>
        </select>
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
        <MessageList messages={searchResults.sort(sortResults)} />
      </div>
    </div>
  );
}
