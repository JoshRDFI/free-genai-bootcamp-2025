import { Button } from "@/components/ui/button"
import { Link } from "react-router-dom"

interface Activity {
  id: number
  title: string
  thumbnail: string
  description: string
  launchUrl: string
}

export default function StudyActivityCard({ activity }: { activity: Activity }) {
  return (
    <article className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden transition-transform hover:scale-105">
      <img 
        src={activity.thumbnail}
        alt={`${activity.title} thumbnail`}
        className="w-full h-48 object-cover"
        loading="lazy"
      />
      
      <div className="p-4 space-y-4">
        <h2 className="text-xl font-semibold dark:text-gray-100">
          {activity.title}
        </h2>
        
        <p className="text-gray-600 dark:text-gray-300">
          {activity.description}
        </p>
        
        <div className="flex gap-3 flex-wrap">
          <Button asChild variant="outline" className="flex-1">
            <a
              href={`${activity.launchUrl}?group_id=4`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-center"
            >
              Launch
            </a>
          </Button>
          
          <Button asChild className="flex-1">
            <Link 
              to={`/study-activties/${activity.id}`}
              className="text-center"
            >
              View Details
            </Link>
          </Button>
        </div>
      </div>
    </article>
  )
}