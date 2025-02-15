import React from 'react';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { PaginationControls } from './PaginationControls';
import { useWords } from '../services/api';

interface WordsTableProps {
  groupId?: number;
}

const WordsTable: React.FC<WordsTableProps> = ({ groupId }) => {
  const { words, loading, error, page, setPage, totalPages } = useWords(groupId);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Japanese</TableHead>
            <TableHead>Romaji</TableHead>
            <TableHead>English</TableHead>
            <TableHead># Correct</TableHead>
            <TableHead># Wrong</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {words.map((word) => (
            <TableRow key={word.id}>
              <TableCell>
                <span className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded-full bg-green-500" />
                  <Link to={`/words/${word.id}`} className="text-blue-600 hover:underline dark:text-blue-400">
                    {word.kanji}
                  </Link>
                </span>
              </TableCell>
              <TableCell>{word.romaji}</TableCell>
              <TableCell>{word.english}</TableCell>
              <TableCell>{word.correct_count}</TableCell>
              <TableCell>{word.wrong_count}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <PaginationControls page={page} setPage={setPage} totalPages={totalPages} />
    </div>
  );
};

export { WordsTable };