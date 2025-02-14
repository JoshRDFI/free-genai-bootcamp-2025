import { Link, useParams } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"

const mockGroup = {
  id: 4,
  name: "Core Verbs",
  description: "Essential verbs for daily conversation",
  words: [
    { id: 1, japanese: "食べる", romaji: "taberu", english: "to eat" },
    { id: 2, japanese: "飲む", romaji: "nomu", english: "to drink" },
    { id: 3, japanese: "行く", romaji: "iku", english: "to go" }
  ],
  sessions: [
    {
      id: 45,
      activity: "Adventure MUD",
      date: new Date("2025-02-13T14:30:00"),
      duration: 45,
      accuracy: 82
    }
  ]
}

export default function WordGroupShowPage() {
  const { id } = useParams()

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Group Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold dark:text-gray-100">
              {mockGroup.name}
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-300">
              {mockGroup.description}
            </p>
            <p className="mt-2 text-gray-600 dark:text-gray-300">
              Total Words: {mockGroup.words.length}
            </p>
          </div>
          <Button asChild>
            <Link to={`/study-activties?group_id=${mockGroup.id}`}>
              Start Study Session
            </Link>
          </Button>
        </div>
      </div>

      {/* Words in Group */}
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold dark:text-gray-100">Words</h2>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Japanese</TableHead>
              <TableHead>Romaji</TableHead>
              <TableHead>English</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {mockGroup.words.map((word) => (
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
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Recent Sessions */}
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold dark:text-gray-100">Recent Sessions</h2>
        {mockGroup.sessions.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Activity</TableHead>
                <TableHead>Date</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Accuracy</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockGroup.sessions.map((session) => (
                <TableRow key={session.id}>
                  <TableCell className="dark:text-gray-300">
                    {session.activity}
                  </TableCell>
                  <TableCell className="dark:text-gray-300">
                    {session.date.toLocaleDateString([], {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: true
                    })}
                  </TableCell>
                  <TableCell className="dark:text-gray-300">
                    {session.duration} mins
                  </TableCell>
                  <TableCell className="dark:text-gray-300">
                    {session.accuracy}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <p className="text-gray-500 dark:text-gray-400">
            No recent sessions for this group
          </p>
        )}
      </div>
    </div>
  )
}