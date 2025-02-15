import React from 'react';
import { useParams } from 'react-router-dom';
import { WordsTable } from '@/components/WordsTable';
import { useWordGroup } from '@/services/api';

const WordGroupShowPage: React.FC = () => {
  const { id } = useParams();
  const { wordGroup, loading, error } = useWordGroup(id);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold dark:text-gray-100">{wordGroup.name}</h1>
      <p className="text-lg text-gray-600 dark:text-gray-300"># Words: {wordGroup.words_count}</p>
      <WordsTable groupId={parseInt(id)} />
    </div>
  );
};

export default WordGroupShowPage;