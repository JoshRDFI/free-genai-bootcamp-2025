import React from 'react';
import { Button } from '@/components/ui/button';

interface PaginationControlsProps {
  page: number;
  setPage: (page: number) => void;
  totalPages: number;
}

const PaginationControls: React.FC<PaginationControlsProps> = ({ page, setPage, totalPages }) => {
  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
    }
  };

  return (
    <div className="flex items-center justify-center space-x-2 mt-4">
      <Button onClick={() => handlePageChange(page - 1)} disabled={page === 1}>
        Previous
      </Button>
      <span className="text-gray-600 dark:text-gray-300">{page}</span>
      <Button onClick={() => handlePageChange(page + 1)} disabled={page === totalPages}>
        Next
      </Button>
    </div>
  );
};

export { PaginationControls };