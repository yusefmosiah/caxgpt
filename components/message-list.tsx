import React from 'react';

interface Message {
  id: string;
  content: string;
  created_at: string; // Assuming ISO string format
  voice?: number;
  similarity_score?: number;
  reranking_score?: number;
  revisions_count?: number;
}

interface MessageListProps {
  messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  // Helper function to format dates
  const formatDate = (isoString: string) => {
    return new Date(isoString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="message-list">
      {messages.length > 0 ? (
        messages.map((message) => (
          <div key={message.id} className="message-item p-4 mb-2 border rounded shadow-sm">
            <p className="message-content text-lg font-semibold mb-2">{message.content}</p>
            <div className="message-details text-sm text-gray-600">
              <p>Created At: {formatDate(message.created_at)}</p>
              {message.voice && <p>Voice: {message.voice}</p>}
              {message.similarity_score && <p>Similarity Score: {message.similarity_score}</p>}
              {message.reranking_score && <p>Reranking Score: {message.reranking_score}</p>}
              {message.revisions_count && <p>Revisions Count: {message.revisions_count}</p>}
            </div>
          </div>
        ))
      ) : (
        <p className="text-center text-gray-500">No messages found.</p>
      )}
    </div>
  );
};

export default MessageList;
