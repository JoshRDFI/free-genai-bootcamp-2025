import { useState } from 'react'
import WordsTable from '@/components/WordsTable'
import PaginationControls from '@/components/PaginationControls'

// Mock data - replace with API calls in real implementation
const mockWords = Array.from({ length: 50 }, (_, i) => ({
  id: i + 1,
  japanese: `日本語${i}`,
  romaji: `nihongo${i}`,
  english: `Japanese${i}`,
  correct: Math.floor(Math.random() * 100),
  wrong: Math.floor(Math.random() * 50),
  audio: `/audio/word${i}.mp3`
}))

export default function WordsPage() {
  const [currentPage, setCurrentPage] = useState(1)
  const totalPages = 28 // Mock total pages

  // Mock audio play function
  const playAudio = (url: string) => {
    new Audio(url).play().catch(() => {
      console.error('Error playing audio')
    })
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold dark:text-gray-100">Words Index</h1>
      </div>

      <WordsTable 
        words={mockWords} 
        playAudio={playAudio} 
      />

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
        className="mt-6"
      />

      {mockWords.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 text-lg">
            No words found
          </p>
        </div>
      )}
    </div>
  )
}