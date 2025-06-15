import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { useWordGroups, useGroup } from '@/services/api';

interface Word {
  id: number;
  kanji: string;
  romaji: string;
  english: string;
  parts: Record<string, string>;
  correct_count: number;
  wrong_count: number;
}

interface Group {
  id: number;
  name: string;
  words: Word[];
}

const WordGroupDetailPage: React.FC = () => {
  const { groupId } = useParams();
  const navigate = useNavigate();
  const { wordGroups, loading, error } = useWordGroups();
  const { group } = useGroup(groupId);
  const wordGroup = wordGroups.find(g => g.id === Number(groupId)) as Group | undefined;

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  if (!wordGroup) return <div>Group not found</div>;

  const handleStartQuiz = () => {
    navigate(`/quiz/${groupId}`);
  };

  const handleStartKanjiWriting = () => {
    navigate(`/kanji-writing/${groupId}`);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold dark:text-gray-100">{wordGroup.name}</h1>
          <div className="space-x-4">
            <Button onClick={handleStartQuiz}>
              Start Quiz
            </Button>
            <Button onClick={handleStartKanjiWriting}>
              Start Kanji Writing Practice
            </Button>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Words in this Group</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {wordGroup.words.map((word) => (
              <div
                key={word.id}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
              >
                <p className="text-2xl font-bold mb-2">{word.kanji}</p>
                <p className="text-gray-600 dark:text-gray-300">{word.romaji}</p>
                <p className="text-gray-800 dark:text-gray-200">{word.english}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WordGroupDetailPage; 