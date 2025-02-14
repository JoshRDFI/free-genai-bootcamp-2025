import { Link, useParams } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"

// Mock data - replace with API calls in real implementation
const mockActivity = {
  id: 1,
  title: "Adventure MUD",
  thumbnail: "/thumbnails/adventure-mud.jpg",
  description: "Text-based RPG for vocabulary building",
  launchUrl: "http://localhost:8081",
  sessions: [
    {
      id: 45,
      groupId: 4,
      groupName: "Core Verbs",
      startTime: new Date("2025-02-13T14:30:00"),
      endTime: new Date("2025-02-13T15:15:00"),
      reviewItems: 82
    },
    {
      id: 44,
      groupId: 4,
      groupName: "Core Verbs",
      startTime: new Date("2025-02-12T09:15:00"),
      endTime: new Date("2025-02-12T10:00:00"),
      reviewItems: 75
    }
  ]
}

function formatDateTime(date: Date): string {
  return date.toLocaleString([], {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  }).replace(',', '')
}

export default function StudyActivityShowPage() {
  const { id } = useParams()
  const activity = mockActivity // In real app, fetch by ID

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Activity Header */}
      <div className="flex flex-col md:flex-row gap-8">
        <img
          src={activity.thumbnail}
          alt={activity.title}
          className="w-full md:w-1/3 rounded-lg shadow-md"
        />
        
        <div className="space-y-4 flex-1">
          <h1 className="text-3xl font-bold dark:text-gray-100">
            {activity.title}
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            {activity.description}
          </p>
          <Button asChild className="w-full md:w-auto">
            <a
              href={`${activity.launchUrl}?group_id=4`}
              target="_blank"
              rel="noopener noreferrer"
            >
              Launch Activity
            </a>
          </Button>
        </div>
      </div>

      {/* Session History */}
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold dark:text-gray-100">
          Session History
        </h2>
        
        {activity.sessions.length > 0 ? (
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
              {activity.sessions.map((session) => {
                const duration = Math.round(
                  (session.endTime.getTime() - session.startTime.getTime()) / 60000
                )
                
                return (
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
                      {formatDateTime(session.startTime)}
                    </TableCell>
                    <TableCell>
                      {formatDateTime(session.endTime)}
                    </TableCell>
                    <TableCell>{session.reviewItems}</TableCell>
                    <TableCell>{duration} minutes</TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">
              No sessions recorded yet
            </p>
          </div>
        )}
      </div>
    </div>
  )
}