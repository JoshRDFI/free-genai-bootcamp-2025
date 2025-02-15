import React from 'react';
import { WordsTable } from '@/components/WordsTable';

const WordsPage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold dark:text-gray-100">Words</h1>
      <WordsTable />
    </div>
  );
};

export default WordsPage;