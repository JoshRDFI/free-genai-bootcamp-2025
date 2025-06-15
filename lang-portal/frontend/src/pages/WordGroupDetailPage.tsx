import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { useWordGroups } from '@/services/api';

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
  const wordGroup = wordGroups.find(g => g.id === Number(groupId)) as Group | undefined;

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;
  if (!wordGroup) return <p>Group not found</p>;

  const handleStartQuiz = () => {
    navigate(`/quiz/${groupId}`);
  };

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold dark:text-gray-100">{wordGroup.name}</h1>
        <Button onClick={handleStartQuiz}>
          Start Quiz
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Kanji</TableHead>
            <TableHead>Romaji</TableHead>
            <TableHead>English</TableHead>
            <TableHead>Parts</TableHead>
            <TableHead>Correct</TableHead>
            <TableHead>Wrong</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {wordGroup.words.map((word: Word) => (
            <TableRow key={word.id}>
              <TableCell>{word.kanji}</TableCell>
              <TableCell>{word.romaji}</TableCell>
              <TableCell>{word.english}</TableCell>
              <TableCell>
                {Object.entries(word.parts).map(([key, value]) => (
                  <span key={key} className="mr-2">
                    {key}: {String(value)}
                  </span>
                ))}
              </TableCell>
              <TableCell>{word.correct_count}</TableCell>
              <TableCell>{word.wrong_count}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default WordGroupDetailPage; 