import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import wordsData from '@/data/words.json';

interface Word {
  kanji: string;
  romaji: string;
  english: string;
  level: string;
  group_id: number;
  category: string;
}

interface Group {
  id: number;
  name: string;
  words: Word[];
  level: string;
}

const WordGroupsPage: React.FC = () => {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [selectedLevel, setSelectedLevel] = useState<string>('');

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        setLoading(true);
        // Group words by category
        const groupedWords = wordsData.reduce((acc: { [key: string]: Word[] }, word: Word) => {
          if (!acc[word.category]) {
            acc[word.category] = [];
          }
          acc[word.category].push(word);
          return acc;
        }, {});

        // Convert to array of groups
        const groupsArray = Object.entries(groupedWords).map(([name, words]) => ({
          id: words[0].group_id,
          name,
          words,
          level: words[0].level,
        }));

        // Sort groups by JLPT level (N5 to N1)
        const sortedGroups = groupsArray.sort((a, b) => {
          const levelOrder = { 'N5': 1, 'N4': 2, 'N3': 3, 'N2': 4, 'N1': 5 };
          return levelOrder[a.level as keyof typeof levelOrder] - levelOrder[b.level as keyof typeof levelOrder];
        });

        setGroups(sortedGroups);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch groups'));
      } finally {
        setLoading(false);
      }
    };

    fetchGroups();
  }, []);

  const filteredGroups = selectedLevel
    ? groups.filter(group => group.level === selectedLevel)
    : groups;

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold dark:text-gray-100">Word Groups</h1>
        <div className="space-x-2">
          <label className="text-sm font-medium">Filter by Level:</label>
          <select
            value={selectedLevel}
            onChange={(e) => setSelectedLevel(e.target.value)}
            className="border rounded px-2 py-1"
          >
            <option value="">All Levels</option>
            <option value="N5">N5</option>
            <option value="N4">N4</option>
            <option value="N3">N3</option>
            <option value="N2">N2</option>
            <option value="N1">N1</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredGroups.map((group) => (
          <div
            key={group.id}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden"
          >
            <div className="p-4 border-b dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
                {group.name}
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {group.words.length} words • Level {group.level}
              </p>
            </div>
            <div className="p-4">
              <ul className="space-y-2">
                {group.words.slice(0, 5).map((word, index) => (
                  <li key={index} className="text-gray-600 dark:text-gray-300">
                    {word.kanji} ({word.romaji}) - {word.english}
                  </li>
                ))}
                {group.words.length > 5 && (
                  <li className="text-blue-600 dark:text-blue-400">
                    <Link to={`/word-groups/${group.id}`}>
                      View all {group.words.length} words →
                    </Link>
                  </li>
                )}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WordGroupsPage;