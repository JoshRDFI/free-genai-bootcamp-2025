import React from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { useStudyActivity } from '@/services/api';
import { formatDateTime } from '@/utils';

const StudyActivityShowPage: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { studyActivity, loading, error } = useStudyActivity(id);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;
  if (!studyActivity) return <p>Activity not found</p>;

  const sessions = studyActivity.sessions || [];
  const isQuiz = studyActivity.name === "Vocabulary Quiz";
  const isSentenceConstructor = studyActivity.name === "Sentence Construction";
  const isKanjiWriting = studyActivity.name === "Kanji Writing Practice";
  const isListening = studyActivity.name === "Listening Comprehension";

  const handleLaunchActivity = () => {
    if (isQuiz) {
      // For quiz, navigate to quiz page with select parameter
      navigate('/quiz/select');
    } else if (isSentenceConstructor) {
      // For sentence constructor, navigate to the sentence constructor page
      navigate('/sentence-constructor');
    } else if (isKanjiWriting) {
      // For kanji writing, navigate to selection page
      navigate('/kanji-writing/select');
    } else if (isListening) {
      // For listening comprehension, navigate to the listening page
      navigate('/listening');
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <div className="flex flex-col md:flex-row gap-8">
        <img
          src={`http://localhost:5000${studyActivity.thumbnail}`}
          alt={studyActivity.name}
          className="w-full md:w-1/3 rounded-lg shadow-md"
        />
        <div className="space-y-4 flex-1">
          <h1 className="text-3xl font-bold dark:text-gray-100">{studyActivity.name}</h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">{studyActivity.description}</p>
          
          {isQuiz && (
            <div className="bg-blue-50 dark:bg-blue-900/30 p-4 rounded-lg">
              <h3 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">How it works:</h3>
              <ol className="list-decimal list-inside space-y-2 text-blue-700 dark:text-blue-300">
                <li>Select a word group to quiz yourself on</li>
                <li>Answer multiple choice questions about the words</li>
                <li>Get immediate feedback on your answers</li>
                <li>Track your progress over time</li>
              </ol>
            </div>
          )}
          
          <Button 
            onClick={handleLaunchActivity} 
            className="w-full md:w-auto"
          >
            {isQuiz ? "Start Quiz" : 
             isSentenceConstructor ? "Start Sentence Constructor" : 
             isKanjiWriting ? "Start Kanji Writing" : 
             isListening ? "Start Listening Exercise" :
             "Launch Activity"}
          </Button>
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-2xl font-bold dark:text-gray-100 mb-4">Recent Sessions</h2>
        {sessions.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Group</TableHead>
                <TableHead>Start Time</TableHead>
                <TableHead>End Time</TableHead>
                <TableHead>Score</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sessions.map((session) => (
                <TableRow key={session.id}>
                  <TableCell>{session.group.name}</TableCell>
                  <TableCell>{formatDateTime(new Date(session.created_at))}</TableCell>
                  <TableCell>{formatDateTime(new Date(session.updated_at))}</TableCell>
                  <TableCell>
                    {session.review_items.length > 0 && (
                      `${session.review_items.filter(item => item.correct).length}/${session.review_items.length}`
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <p className="text-gray-600 dark:text-gray-400">No sessions yet. Start practicing to see your progress!</p>
        )}
      </div>
    </div>
  );
};

export default StudyActivityShowPage;