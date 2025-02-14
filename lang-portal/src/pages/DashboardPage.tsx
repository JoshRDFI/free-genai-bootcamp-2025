import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Link } from "react-router-dom"

// Mock data - replace with API calls in real implementation
const mockStats = {
  totalWords: 1428,
  accuracy: 82,
  dailyGoal: 65,
  lastSession: {
    groupName: "Core Verbs",
    groupId: 4,
    startTime: new Date("2025-02-13T14:30:00"),
    endTime: new Date("2025-02-13T15:15:00"),
    reviewItems: 45,
    status: "completed" as "active" | "completed"
  }
}

export default function DashboardPage() {
  const duration = Math.round(
    (mockStats.lastSession.endTime.getTime() - mockStats.lastSession.startTime.getTime()) / 60000
  )

  return (
    <div className="space-y-6">
      {/* Stats Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Total Words Studied</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold dark:text-gray-100">
              {mockStats.totalWords.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Average Accuracy</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold dark:text-gray-100">
              {mockStats.accuracy}%
            </div>
            <Progress value={mockStats.accuracy} className="h-2 mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Daily Goal Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold dark:text-gray-100">
              {mockStats.dailyGoal}/100 words
            </div>
            <Progress value={mockStats.dailyGoal} className="h-2 mt-2" />
          </CardContent>
        </Card>
      </div>

      {/* Last Session Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Last Session</CardTitle>
        </CardHeader>
        <CardContent>
          {mockStats.lastSession ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium dark:text-gray-100">
                    Group:{" "}
                    <Link 
                      to={`/word-groups/${mockStats.lastSession.groupId}`}
                      className="text-blue-600 hover:underline dark:text-blue-400"
                    >
                      {mockStats.lastSession.groupName}
                    </Link>
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {mockStats.lastSession.startTime.toLocaleString([], {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: true
                    })} - {duration} minutes
                  </p>
                </div>
                {mockStats.lastSession.status === "active" && (
                  <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors">
                    Continue Session
                  </button>
                )}
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Review Items</p>
                  <p className="font-medium dark:text-gray-100">
                    {mockStats.lastSession.reviewItems}
                  </p>
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-500 dark:text-gray-400">Accuracy</p>
                  <p className="font-medium dark:text-gray-100">82%</p>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">
              No recent sessions available
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}