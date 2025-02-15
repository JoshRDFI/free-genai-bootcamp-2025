import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

interface StudyActivityCardProps {
  id: number;
  title: string;
  thumbnail: string;
  description: string;
  launchUrl: string;
}

const StudyActivityCard: React.FC<StudyActivityCardProps> = ({ id, title, thumbnail, description, launchUrl }) => {
  return (
    <div className="max-w-sm rounded-lg overflow-hidden shadow-lg bg-white dark:bg-gray-800">
      <img className="w-full" src={thumbnail} alt={title} />
      <div className="px-6 py-4">
        <div className="font-bold text-xl mb-2 dark:text-gray-100">{title}</div>
        <p className="text-gray-700 dark:text-gray-300 text-base">{description}</p>
      </div>
      <div className="px-6 pt-4 pb-2">
        <Button asChild className="w-full">
          <a href={`${launchUrl}${id}`} target="_blank" rel="noopener noreferrer">Launch Activity</a>
        </Button>
        <Button asChild className="w-full mt-2">
          <Link to={`/study-activities/${id}`}>View</Link>
        </Button>
      </div>
    </div>
  );
};

export { StudyActivityCard };