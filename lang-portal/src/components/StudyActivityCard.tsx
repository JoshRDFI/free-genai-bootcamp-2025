import { Button } from "@/components/ui/button"

export default function StudyActivityCard({ activity }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
      <img 
        src={activity.thumbnail} 
        alt={activity.title}
        className="w-full h-48 object-cover"
      />
      
      <div className="p-4 space-y-4">
        <h3 className="text-xl font-semibold dark:text-gray-100">
          {activity.title}
        </h3>
        
        <div className="flex gap-3">
          <Button asChild variant="outline">
            <a 
              href={`${activity.launchUrl}?group_id=4`} // group_id should be dynamic
              target="_blank"
              rel="noopener noreferrer"
            >
              Launch
            </a>
          </Button>
          
          <Button asChild>
            <a href={`/study-activties/${activity.id}`}>
              View
            </a>
          </Button>
        </div>
      </div>
    </div>
  )
}