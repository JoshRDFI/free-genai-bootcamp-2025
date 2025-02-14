import { Link } from "react-router-dom"
import StudyActivityCard from "@/components/StudyActivityCard"

// Mock data - replace with API data in real implementation
const mockActivities = [
  {
    id: 1,
    title: "Adventure MUD",
    thumbnail: "/thumbnails/adventure-mud.jpg",
    description: "Text-based RPG for vocabulary building",
    launchUrl: "http://localhost:8081"
  },
  {
    id: 2,
    title: "Typing Tutor",
    thumbnail: "/thumbnails/typing-tutor.jpg",
    description: "Improve typing speed with Japanese vocabulary",
    launchUrl: "http://localhost:8082"
  },
  {
    id: 3,
    title: "Flash Cards",
    thumbnail: "/thumbnails/flash-cards.jpg",
    description: "Traditional flash card drilling system",
    launchUrl: "http://localhost:8083"
  }
]

export default function StudyActivitiesPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 dark:text-gray-100">Study Activities</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {mockActivities.map((activity) => (
          <StudyActivityCard 
            key={activity.id}
            activity={activity}
          />
        ))}
      </div>

      {/* Empty state */}
      {mockActivities.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 text-lg">
            No study activities available.{" "}
            <Link to="/settings" className="text-blue-600 hover:underline dark:text-blue-400">
              Contact admin
            </Link>
          </p>
        </div>
      )}
    </div>
  )
}