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
              <Link to={`/words/${word.id}`} className="text-blue-600 hover:underline">
                {word.japanese}
              </Link>
              <button 
                onClick={() => playAudio(word.audio)}
                className="ml-2 text-gray-500 hover:text-blue-600"
              >
                ▶
              </button>
            </TableCell>
            <TableCell>{word.romaji}</TableCell>
            <TableCell>{word.english}</TableCell>
            <TableCell>{word.correct}</TableCell>
            <TableCell>{word.wrong}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}