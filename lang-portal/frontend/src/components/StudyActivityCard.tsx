import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

interface StudyActivityCardProps {
  id: number;
  name: string;
  thumbnail: string;
  description: string;
  url: string;
}

export const StudyActivityCard: React.FC<StudyActivityCardProps> = ({
  id,
  name,
  thumbnail,
  description,
  url,
}) => {
  const navigate = useNavigate();

  const handleLaunchActivity = () => {
    if (name === "Vocabulary Quiz") {
      // For quiz, navigate to quiz page with select parameter
      navigate('/quiz/select');
    } else if (name === "Sentence Construction") {
      // For sentence constructor, navigate to the sentence constructor page
      navigate('/sentence-constructor');
    } else if (name === "Kanji Writing Practice") {
      // For kanji writing, navigate to selection page
      navigate('/kanji-writing/select');
    } else if (url) {
      // Only use window.open for activities with a valid URL
      window.open(url, '_blank');
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden">
      <img
        src={`http://localhost:5000${thumbnail}`}
        alt={name}
        className="w-full h-48 object-cover"
      />
      <div className="p-4">
        <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-100 mb-2">{name}</h2>
        <p className="text-gray-600 dark:text-gray-300 mb-4">{description}</p>
        <div className="flex justify-between">
          <Link
            to={`/study-activities/${id}`}
            className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
          >
            View Details
          </Link>
          <button
            onClick={handleLaunchActivity}
            className="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
          >
            Launch Activity
          </button>
        </div>
      </div>
    </div>
  );
};