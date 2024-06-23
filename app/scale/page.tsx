"use client";
import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export default function ScalePage() {
  const [userPrompt, setUserPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const res = await fetch("/api/vowel_loop", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_prompt: userPrompt }),
      });

      if (!res.ok) {
        throw new Error("Failed to get response from Vowel Loop");
      }

      const data = await res.json();
      setResponse(data.response);
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
      <h1 className="text-4xl font-bold mb-4">Vowel Loop</h1>
      <form onSubmit={handleSubmit} className="w-full max-w-lg space-y-4">
        <textarea
          value={userPrompt}
          onChange={(e) => setUserPrompt(e.target.value)}
          placeholder="Enter your prompt"
          className="w-full p-4 text-lg bg-gray-800 text-white placeholder-gray-400 border-0 rounded-md focus:ring-2 focus:ring-blue-500"
          rows={6}
        />
        <Button type="submit" disabled={isLoading} className="w-full bg-blue-500 text-white p-4 rounded-md hover:bg-blue-600 disabled:bg-blue-400">
          {isLoading ? "Processing..." : "Submit"}
        </Button>
      </form>
      {error && <p className="text-red-500 mt-4">{error}</p>}
      {response && <div className="mt-8 w-full max-w-3xl bg-gray-800 p-4 rounded-md">
        <h2 className="text-2xl font-bold mb-2">Response</h2>
        <p>{response}</p>
      </div>}
    </div>
  );
}
