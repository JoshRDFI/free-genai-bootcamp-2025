import { useState } from "react"
import { Link } from "react-router-dom"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"
import PaginationControls from "@/components/PaginationControls"

interface Session {
  id: number
  activity: string 
  duration: number
  date: Date
  accuracy: number
  groupId: number
  wordReviews: {
    wordId: number
    correct: boolean
  }[]
}

const mockSessions = Array.from({ length: 50 }, (_, i) => ({
  id: i + 1,
  activity: ["Adventure MUD", "Typing Tutor", "Flash Cards"][i % 3],
  duration: Math.floor(Math.random() * 60) + 15,
  date: new Date(2025, 1, Math.floor(Math.random() * 14 + 1)),
  accuracy: Math.floor(Math.random() * 100),
  groupId: 4
}))

export default function SessionsPage() {
  const [currentPage, setCurrentPage] = useState(1)
  const totalPages = 10

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold dark:text-gray-100">Study Sessions</h1>
      </div>

      <Table className="border rounded-lg overflow-hidden">
        <TableHeader className="bg-gray-50 dark:bg-gray-800">
          <TableRow>
            <TableHead>Activity</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Group</TableHead>
            <TableHead>Accuracy</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {mockSessions.map((session) => (
            <TableRow key={session.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
              <TableCell className="py-4 px-6 dark:text-gray-300">
                <Link
                  to={`/sessions/${session.id}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  {session.activity}
                </Link>
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
              <TableCell className="dark:text-gray-300">{session.duration} mins</TableCell>
              <TableCell className="dark:text-gray-300">
                <Link
                  to={`/word-groups/${session.groupId}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  Group {session.groupId}
                </Link>
              </TableCell>
              <TableCell className="dark:text-gray-300">
                <div className="flex items-center gap-2">
                  <span>{session.accuracy}%</span>
                  <Progress value={session.accuracy} className="h-2 w-24" />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
        className="mt-6"
      />
    </div>
  )
}