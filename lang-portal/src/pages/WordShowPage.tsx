import { Link, useParams } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"

// Mock data - replace with API calls in real implementation
const mockWord = {
  id: 1,
  japanese: "始める",
  romaji: "hajimeru",
  english: "to begin",
  correct: 42,
  wrong: 8,
  audio: "/audio/begin.mp3",
  history: [
    {
      id: 145,
      sessionId: 45,
      groupId: 4,
      groupName: "Core Verbs",
      date: new Date("2025-02-13T14:35:00"),
      correct: true
    },
    {
      id: 132,
      sessionId: 32,
      groupId: 4,
      groupName: "Core Verbs",
      date: new Date("2025-02-12T09:20:00"),
      correct: false
    }
  ]
}

export default function WordShowPage() {
  const { id } = useParams()
  const word = mockWord // In real app, fetch by ID

  const playAudio = () => {
    new Audio(word.audio).play().catch(() => {
      console.error('Error playing audio')
    })
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Word Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold dark:text-gray-100 flex items-center gap-4">
              {word.japanese}
              <button
                onClick={playAudio}
                className="text-2xl p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                aria-label="Play pronunciation"
              >
                ▶
              </button>
            </h1>
            <div className="mt-2 space-y-1">
              <p className="text-lg text-gray-600 dark:text-gray-300">
                {word.romaji}
              </p>
              <p className="text-lg text-gray-600 dark:text-gray-300">
                {word.english}
              </p>
            </div>
          </div>
          <div className="text-right space-y-2">
            <p className="text-green-600 dark:text-green-400 font-medium">
              Correct: {word.correct}
            </p>
            <p className="text-red-600 dark:text-red-400 font-medium">
              Wrong: {word.wrong}
            </p>
          </div>
        </div>
      </div>

      {/* Review History */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold dark:text-gray-100">
            Review History
          </h2>
          <Button asChild variant="outline">
            <Link to="/words">Back to All Words</Link>
          </Button>
        </div>
        
        {word.history.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Group</TableHead>
                <TableHead>Session</TableHead>
                <TableHead>Result</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {word.history.map((review) => (
                <TableRow key={review.id}>
                  <TableCell className="dark:text-gray-300">
                    {review.date.toLocaleDateString([], {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: true
                    })}
                  </TableCell>
                  <TableCell className="dark:text-gray-300">
                    <Link
                      to={`/word-groups/${review.groupId}`}
                      className="text-blue-600 hover:underline dark:text-blue-400"
                    >
                      {review.groupName}
                    </Link>
                  </TableCell>
                  <TableCell className="dark:text-gray-300">
                    <Link
                      to={`/sessions/${review.sessionId}`}
                      className="text-blue-600 hover:underline dark:text-blue-400"
                    >
                      Session #{review.sessionId}
                    </Link>
                  </TableCell>
                  <TableCell>
                    {review.correct ? (
                      <span className="text-green-600 dark:text-green-400">✓ Correct</span>
                    ) : (
                      <span className="text-red-600 dark:text-red-400">✗ Wrong</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">
              No review history available
            </p>
          </div>
        )}
      </div>
    </div>
  )
}