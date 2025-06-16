import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import wordsData from '@/data/words.json';

interface Word {
  kanji: string;
  romaji: string;
  english: string;
  level: string;
  group_id: number;
  category: string;
}

const WordGroupDetailPage: React.FC = () => {
  const { groupId } = useParams();
  const navigate = useNavigate();
  const [groupWords, setGroupWords] = useState<Word[]>([]);
  const [groupName, setGroupName] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!groupId) {
      setError('No group ID provided');
      setLoading(false);
      return;
    }

    const numericGroupId = parseInt(groupId, 10);
    if (isNaN(numericGroupId)) {
      setError('Invalid group ID');
      setLoading(false);
      return;
    }

    // Get words for this group from the local data
    const words = wordsData.filter(word => word.group_id === numericGroupId);
    if (words.length === 0) {
      setError('Group not found');
      setLoading(false);
      return;
    }

    // Get the group name from the first word's category
    const groupName = words[0].category.split(' (')[0];
    
    setGroupWords(words);
    setGroupName(groupName);
    setLoading(false);
  }, [groupId]);

  const handleStartQuiz = () => {
    navigate(`/quiz/${groupId}`);
  };

  const handleStartKanjiWriting = () => {
    navigate(`/kanji-writing/${groupId}`);
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!groupWords.length) return <div>No words found in this group</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold dark:text-gray-100">{groupName}</h1>
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
            {groupWords.map((word, index) => (
              <div
                key={index}
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