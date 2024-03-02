export type Message = {
    id: string;
    content: string;
    similarity_score: number;
    reranking_score?: number;
    voice?: number;
    revisions_count?: number;
    created_at?: string;
  };
