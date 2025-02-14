import { useState } from "react"
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from "@/components/ui/table"

type SortDirection = 'asc' | 'desc'
type SortableColumns = 'japanese' | 'romaji' | 'english' | 'correct' | 'wrong'

export default function WordsTable({ words }) {
  const [sortColumn, setSortColumn] = useState<SortableColumns>('japanese')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  const handleSort = (column: SortableColumns) => {
    if (column === sortColumn) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column)
      setSortDirection('asc')
    }
  }

  const getSortIndicator = (column: SortableColumns) => {
    if (column === sortColumn) {
      return sortDirection === 'asc' ? ' ↓' : ' ↑'
    }
    return ''
  }

  return (
    <Table className="mt-6">
      <TableHeader>
        <TableRow>
          {['Japanese', 'Romaji', 'English', '# Correct', '# Wrong'].map((header) => (
            <TableHead
              key={header}
              className="cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort(header.toLowerCase().replace(' ', '_') as SortableColumns)}
            >
              {header}
              {getSortIndicator(header.toLowerCase().replace(' ', '_') as SortableColumns)}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {words.map((word) => (
          <TableRow key={word.id}>
            <TableCell>
              <div className="flex items-center">
                <Link 
                  to={`/words/${word.id}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  {word.japanese}
                </Link>
                <button
                  onClick={() => playAudio(word.audio)}
                  className="ml-2 p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  aria-label="Play pronunciation"
                >
                  ▶
                </button>
              </div>
            </TableCell>
            <TableCell className="py-4 px-6 dark:text-gray-300">{word.romaji}</TableCell>
            <TableCell className="py-4 px-6 dark:text-gray-300">{word.english}</TableCell>
            <TableCell className="py-4 px-6 dark:text-gray-300">{word.correct}</TableCell>
            <TableCell className="py-4 px-6 dark:text-gray-300">{word.wrong}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}