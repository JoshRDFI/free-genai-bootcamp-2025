import { Link, useParams } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"
import { Progress } from "@/components/ui/progress"

// Mock data - replace with API calls in real implementation
const mockSession = {
  id: 45,
  activity: "Adventure MUD",
  groupId: 4,
  groupName: "Core Verbs",
  duration: 45,
  date: new Date("2025-02-13T14:30:00"),
  accuracy: 82,
  words: [
    { id: 1, japanese: "始める", romaji: "hajimeru", english: "to begin", correct: true },
    { id: 2, japanese: "食べる", romaji: "taberu", english: "to eat", correct: true },
    { id: 3, japanese: "飲む", romaji: "nomu", english: "to drink", correct: false }
  ]
}

export default function SessionShowPage() {
  const { id } = useParams()

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Session Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold dark:text-gray-100">
              {mockSession.activity} Session
            </h1>
            <div className="mt-4 space-y-2">
              <p className="text-gray-600 dark:text-gray-300">
                Group:{" "}
                <Link
                  to={`/word-groups/${mockSession.groupId}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  {mockSession.groupName}
                </Link>
              </p>
              <p className="text-gray-600 dark:text-gray-300">
                Date:{" "}
                {mockSession.date.toLocaleDateString([], {
                  year: 'numeric',
                  month: '2-digit',
                  day: '2-digit',
                  hour: '2-digit',
                  minute: '2-digit',
                  hour12: true
                })}
              </p>
              <p className="text-gray-600 dark:text-gray-300">
                Duration: {mockSession.duration} minutes
              </p>
            </div>
          </div>
          <div className="text-right space-y-2">
            <p className="text-lg font-medium dark:text-gray-100">
              Overall Accuracy: {mockSession.accuracy}%
            </p>
            <Progress value={mockSession.accuracy} className="w-48 h-2" />
          </div>
        </div>
      </div>

      {/* Words Reviewed */}
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold dark:text-gray-100">Words Reviewed</h2>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Japanese</TableHead>
              <TableHead>Romaji</TableHead>
              <TableHead>English</TableHead>
              <TableHead>Result</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {mockSession.words.map((word) => (
              <TableRow key={word.id}>
                <TableCell className="dark:text-gray-300">
                  <Link
                    to={`/words/${word.id}`}
                    className="text-blue-600 hover:underline dark:text-blue-400"
                  >
                    {word.japanese}
                  </Link>
                </TableCell>
                <TableCell className="dark:text-gray-300">{word.romaji}</TableCell>
                <TableCell className="dark:text-gray-300">{word.english}</TableCell>
                <TableCell>
                  {word.correct ? (
                    <span className="text-green-600 dark:text-green-400">✓ Correct</span>
                  ) : (
                    <span className="text-red-600 dark:text-red-400">✗ Wrong</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex justify-end">
        <Button asChild variant="outline">
          <Link to="/sessions">Back to All Sessions</Link>
        </Button>
      </div>
    </div>
  )
}