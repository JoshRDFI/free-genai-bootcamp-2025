import React from 'react';
import { StudyActivityCard } from '@/components/StudyActivityCard';
import { useStudyActivities } from '@/services/api';

const StudyActivitiesPage: React.FC = () => {
  const { studyActivities, loading, error } = useStudyActivities();

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error.message}</p>;

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      <h1 className="text-3xl font-bold dark:text-gray-100">Study Activities</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {studyActivities.map((activity) => (
          <StudyActivityCard
            key={activity.id}
            id={activity.id}
            name={activity.name}
            thumbnail={activity.thumbnail}
            description={activity.description}
            url={activity.url}
          />
        ))}
      </div>
    </div>
  );
};

export default StudyActivitiesPage;