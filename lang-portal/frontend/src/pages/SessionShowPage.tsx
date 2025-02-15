import React from 'react';
import { useParams } from 'react-router-dom';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { useSession } from '@/services/api';
import { formatDateTime } from '@/utils';

const SessionShowPage: React.FC = () => {
  const { id } = useParams();
  const { session, loading, error } = useSession(id);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold dark:text-gray-100">Session Details</h1>
      <div className="space-y-4">
        <p className="text-lg text-gray-600 dark:text-gray-300">Group: {session.groupName}</p>
        <p className="text-lg text-gray-600 dark:text-gray-300">Activity: {session.activityName}</p>
        <p className="text-lg text-gray-600 dark:text-gray-300">Start Time: {formatDateTime(session.startTime)}</p>
        <p className="text-lg text-gray-600 dark:text-gray-300">End Time: {formatDateTime(session.endTime)}</p>
        <p className="text-lg text-gray-600 dark:text-gray-300">Duration: {session.duration} minutes</p>
      </div>
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold dark:text-gray-100">Review Items</h2>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Word</TableHead>
              <TableHead>Correct</TableHead>
              <TableHead>Time</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {session.reviewItems.map((review) => (
              <TableRow key={review.id}>
                <TableCell>
                  <Link
                    to={`/words/${review.wordId}`}
                    className="text-blue-600 hover:underline dark:text-blue-400"
                  >
                    {review.wordKanji}
                  </Link>
                </TableCell>
                <TableCell>{review.correct ? 'Yes' : 'No'}</TableCell>
                <TableCell>{formatDateTime(review.time)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
};

export default SessionShowPage;