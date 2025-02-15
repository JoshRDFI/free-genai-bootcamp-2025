import React from 'react';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { useWordGroups } from '@/services/api';
import { PaginationControls } from '@/components/PaginationControls';

const WordGroupsPage: React.FC = () => {
  const { wordGroups, loading, error, page, setPage, totalPages } = useWordGroups();

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold dark:text-gray-100">Word Groups</h1>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Group Name</TableHead>
            <TableHead># Words</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {wordGroups.map((group) => (
            <TableRow key={group.id}>
              <TableCell>
                <Link
                  to={`/word-groups/${group.id}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  {group.name}
                </Link>
              </TableCell>
              <TableCell>{group.words_count}