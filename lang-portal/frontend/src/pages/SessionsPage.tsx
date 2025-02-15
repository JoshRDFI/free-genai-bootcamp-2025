import React from 'react';
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
                  to={`/word-groups/${session.groupId}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  {session.groupName}
                </Link>
              </TableCell>
              <TableCell>
                <Link
                  to={`/study-activities/${session.activityId}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  {session.activityName}
                </Link>
              </TableCell>
              <TableCell>{formatDateTime(session.startTime)}</TableCell>
              <TableCell>{formatDateTime(session.endTime)}</TableCell>
              <TableCell>{session.duration} minutes</TableCell>
              <TableCell>{session.reviewItems.length}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <PaginationControls page={page} setPage={setPage} totalPages={totalPages} />
    </div>
  );
};

export default SessionsPage;