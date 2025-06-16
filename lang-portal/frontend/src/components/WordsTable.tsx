import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { PaginationControls } from './PaginationControls';
import { useWords } from '@/services/api';
import wordsData from '@/data/words.json';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';

interface Word {
  kanji: string;
  romaji: string;
  english: string;
  level: string;
  group_id: number;
  category: string;
}

interface WordsTableProps {
  groupId?: number;
}

export const WordsTable: React.FC<WordsTableProps> = ({ groupId }) => {
  const [words, setWords] = useState<Word[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [sortField, setSortField] = useState<keyof Word>('kanji');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [filterLevel, setFilterLevel] = useState<string>('');
  const itemsPerPage = 10;

  useEffect(() => {
    const fetchWords = async () => {
      try {
        setLoading(true);
        // Filter by group if groupId is provided
        let filteredWords = groupId 
          ? wordsData.filter(word => word.group_id === groupId)
          : wordsData;

        // Apply level filter if set
        if (filterLevel) {
          filteredWords = filteredWords.filter(word => word.level === filterLevel);
        }

        // Sort the words
        filteredWords.sort((a, b) => {
          const aValue = String(a[sortField]);
          const bValue = String(b[sortField]);
          if (sortOrder === 'asc') {
            return aValue.localeCompare(bValue);
          }
          return bValue.localeCompare(aValue);
        });

        setWords(filteredWords);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch words'));
      } finally {
        setLoading(false);
      }
    };

    fetchWords();
  }, [groupId, sortField, sortOrder, filterLevel]);

  const totalPages = Math.ceil(words.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedWords = words.slice(startIndex, startIndex + itemsPerPage);

  const handleSort = (field: keyof Word) => {
    if (field === sortField) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const handleFilterLevel = (event: SelectChangeEvent) => {
    setFilterLevel(event.target.value);
    setCurrentPage(1);
  };

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Filter by Level</InputLabel>
          <Select
            value={filterLevel}
            onChange={handleFilterLevel}
            label="Filter by Level"
            sx={{
              '& .MuiSelect-select': {
                bgcolor: '#f9fafb',
                color: '#374151'
              },
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: '#e5e7eb'
              },
              '&:hover .MuiOutlinedInput-notchedOutline': {
                borderColor: '#374151'
              },
              '& .MuiSelect-icon': {
                color: '#374151'
              }
            }}
            MenuProps={{
              PaperProps: {
                sx: {
                  bgcolor: '#f9fafb',
                  '& .MuiMenuItem-root': {
                    color: '#374151',
                    '&:hover': {
                      bgcolor: '#e5e7eb'
                    }
                  }
                }
              }
            }}
          >
            <MenuItem value="">All Levels</MenuItem>
            <MenuItem value="N5">N5</MenuItem>
            <MenuItem value="N4">N4</MenuItem>
            <MenuItem value="N3">N3</MenuItem>
            <MenuItem value="N2">N2</MenuItem>
            <MenuItem value="N1">N1</MenuItem>
          </Select>
        </FormControl>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead 
              className="cursor-pointer"
              onClick={() => handleSort('kanji')}
            >
              Kanji {sortField === 'kanji' && (sortOrder === 'asc' ? '↑' : '↓')}
            </TableHead>
            <TableHead 
              className="cursor-pointer"
              onClick={() => handleSort('romaji')}
            >
              Romaji {sortField === 'romaji' && (sortOrder === 'asc' ? '↑' : '↓')}
            </TableHead>
            <TableHead 
              className="cursor-pointer"
              onClick={() => handleSort('english')}
            >
              English {sortField === 'english' && (sortOrder === 'asc' ? '↑' : '↓')}
            </TableHead>
            <TableHead 
              className="cursor-pointer"
              onClick={() => handleSort('level')}
            >
              Level {sortField === 'level' && (sortOrder === 'asc' ? '↑' : '↓')}
            </TableHead>
            <TableHead 
              className="cursor-pointer"
              onClick={() => handleSort('category')}
            >
              Category {sortField === 'category' && (sortOrder === 'asc' ? '↑' : '↓')}
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {paginatedWords.map((word, index) => (
            <TableRow key={`${word.kanji}-${index}`}>
              <TableCell>{word.kanji}</TableCell>
              <TableCell>{word.romaji}</TableCell>
              <TableCell>{word.english}</TableCell>
              <TableCell>{word.level}</TableCell>
              <TableCell>{word.category}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
      />
    </div>
  );
};