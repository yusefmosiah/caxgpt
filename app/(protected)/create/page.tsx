"use client";
import React, { useState, useEffect } from "react";
import MessageList from "@/components/message-list";

interface DashboardData {
  messages: Message[];
}

interface Message {
  id: string;
  content: string;
  created_at: string;
}

const CreatePage = () => {
  const [message, setMessage] = useState("");
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null
  );

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await fetch("/api/dashboard", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });
        if (!response.ok) {
          throw new Error("Failed to fetch dashboard data");
        }
        const data: DashboardData = await response.json();
        setDashboardData(data);
      } catch (error) {
        console.error("Error fetching dashboard data:", error);
      }
    };

    fetchDashboardData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await fetch("/api/new_message", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ input_text: message }),
      });
      if (!response.ok) {
        throw new Error("Failed to create message");
      }
      const newMessage: Message = await response.json();
      // Update dashboard data with the new message without reloading the page
      if (dashboardData) {
        setDashboardData({
          ...dashboardData,
          messages: [newMessage, ...dashboardData.messages],
        });
      }
      setMessage("");
    } catch (error) {
      console.error("Error creating message:", error);
    }
  };

  return (
    <div className="flex">
      <div className="w-1/3">
        <h2 className="text-xl font-bold mb-4">Your Messages</h2>
        {dashboardData && <MessageList messages={dashboardData.messages} />}
      </div>
      <div className="w-2/3 p-4">
        <h1 className="text-2xl font-bold mb-4">Create a New Message</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Write your message here..."
            className="w-full p-2 border rounded"
            rows={6}
          />
          <button
            type="submit"
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Submit
          </button>
        </form>
      </div>
    </div>
  );
};

export default CreatePage;
