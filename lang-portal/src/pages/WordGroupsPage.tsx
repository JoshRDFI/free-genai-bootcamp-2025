import { Link } from "react-router-dom"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"
import PaginationControls from "@/components/PaginationControls"

// Mock data
const mockGroups = Array.from({ length: 50 }, (_, i) => ({
  id: i + 1,
  name: `Group ${i + 1}`,
  wordCount: Math.floor(Math.random() * 100),
  lastPracticed: new Date(2025, 1, Math.floor(Math.random() * 14 + 1)),
  accuracy: Math.floor(Math.random() * 100)
}))

export default function WordGroupsPage() {
  const [currentPage, setCurrentPage] = useState(1)
  const totalPages = 10

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold dark:text-gray-100">Word Groups</h1>
      </div>

      <Table className="border rounded-lg overflow-hidden">
        <TableHeader className="bg-gray-50 dark:bg-gray-800">
          <TableRow>
            <TableHead className="w-2/5">Group Name</TableHead>
            <TableHead>Words</TableHead>
            <TableHead>Last Practiced</TableHead>
            <TableHead>Accuracy</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {mockGroups.map((group) => (
            <TableRow key={group.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
              <TableCell className="py-4 px-6">
                <Link
                  to={`/word-groups/${group.id}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  {group.name}
                </Link>
              </TableCell>
              <TableCell className="dark:text-gray-300">{group.wordCount}</TableCell>
              <TableCell className="dark:text-gray-300">
                {group.lastPracticed.toLocaleDateString([], {
                  year: 'numeric',
                  month: '2-digit',
                  day: '2-digit'
                })}
              </TableCell>
              <TableCell className="dark:text-gray-300">
                <div className="flex items-center gap-2">
                  <span>{group.accuracy}%</span>
                  <Progress value={group.accuracy} className="h-2 w-24" />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
        className="mt-6"
      />
    </div>
  )
}