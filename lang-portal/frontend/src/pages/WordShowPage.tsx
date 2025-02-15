import React from 'react';
import { useParams } from 'react-router-dom';
import { useWord } from '@/services/api';

const WordShowPage: React.FC = () => {
  const { id } = useParams();
  const { word, loading, error } = useWord(id);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold dark:text-gray-100">{word.kanji}</h1>
      <p className="text-lg text-gray-600 dark:text-gray-300">Romaji: {word.romaji}</p>
      <p className="text-lg text-gray-600 dark:text-gray-300">English: {word.english}</p>
      <p className="text-lg text-gray-600 dark:text-gray-300"># Correct: {word.correct_count}</p>
      <p className="text-lg text-gray-600 dark:text-gray-300"># Wrong: {word.wrong_count}</p>
    </div>
  );
};

export default WordShowPage;