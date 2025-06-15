import React from 'react';
import { Link } from 'react-router-dom';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { useSessions } from '@/services/api';
import { PaginationControls } from '@/components/PaginationControls';
import { formatDateTime } from '@/utils';

const SessionsPage: React.FC = () => {
  const { sessions, loading, error, page, setPage, totalPages } = useSessions();

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold dark:text-gray-100">Sessions</h1>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Group</TableHead>
            <TableHead>Activity</TableHead>
            <TableHead>Start Time</TableHead>
            <TableHead>End Time</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Review Items</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sessions.map((session) => (
            <TableRow key={session.id}>
              <TableCell>
                <Link
                  to={`/word-groups/${session.group_id}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  {session.group.name}
                </Link>
              </TableCell>
              <TableCell>
                <Link
                  to={`/study-activities/${session.study_activity_id}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  {session.study_activity.name}
                </Link>
              </TableCell>
              <TableCell>{formatDateTime(new Date(session.created_at))}</TableCell>
              <TableCell>{formatDateTime(new Date(session.updated_at))}</TableCell>
              <TableCell>{Math.round((new Date(session.updated_at).getTime() - new Date(session.created_at).getTime()) / (1000 * 60))} minutes</TableCell>
              <TableCell>{session.review_items.length}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <PaginationControls 
        currentPage={page} 
        totalPages={totalPages} 
        onPageChange={setPage} 
      />
    </div>
  );
};

export default SessionsPage;