import React from 'react';
import { useParams } from 'react-router-dom';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { useStudyActivity } from '@/services/api';
import { formatDateTime } from '@/utils';

const StudyActivityShowPage: React.FC = () => {
  const { id } = useParams();
  const { studyActivity, loading, error } = useStudyActivity(id);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <div className="flex flex-col md:flex-row gap-8">
        <img
          src={studyActivity.thumbnail}
          alt={studyActivity.title}
          className="w-full md:w-1/3 rounded-lg shadow-md"
        />
        <div className="space-y-4 flex-1">
          <h1 className="text-3xl font-bold dark:text-gray-100">{studyActivity.title}</h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">{studyActivity.description}</p>
          <Button asChild className="w-full md:w-auto">
            <a
              href={`${studyActivity.launchUrl}${studyActivity.groupId}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              Launch Activity
            </a>
          </Button>
        </div>
      </div>
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold dark:text-gray-100">Session History</h2>
        {studyActivity.sessions.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Group</TableHead>
                <TableHead>Start Time</TableHead>
                <TableHead>End Time</TableHead>
                <TableHead>Review Items</TableHead>
                <TableHead>Duration</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {studyActivity.sessions.map((session) => {
                const duration = Math.round(
                  (session.endTime.getTime() - session.startTime.getTime()) / 60000
                );
                return (
                  <TableRow key={session.id}>
                    <TableCell>
                      <span className="flex items-center gap-2">
                        <span className={`h-3 w-3 rounded-full ${session.endTime ? 'bg-green-500' : 'bg-yellow-500'}`} />
                        <Link
                          to={`/word-groups/${session.groupId}`}
                          className="text-blue-600 hover:underline dark:text-blue-400"
                        >
                          {session.groupName}
                        </Link>
                      </span>
                    </TableCell>
                    <TableCell>{formatDateTime(session.startTime)}</TableCell>
                    <TableCell>{formatDateTime(session.endTime)}</TableCell>
                    <TableCell>{session.reviewItems}</TableCell>
                    <TableCell>{duration} minutes</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        ) : (
          <div className="text-center py-8 border-2 border-dashed rounded-lg">
            <p className="text-muted-foreground mb-4">No sessions recorded yet</p>
            <Button asChild variant="outline">
              <Link to="/word-groups">Choose a Word Group to Start</Link>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudyActivityShowPage;