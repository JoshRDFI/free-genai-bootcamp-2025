import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'

export default function SettingsPage() {
  const [darkMode, setDarkMode] = useState(false)
  const [confirmationText, setConfirmationText] = useState('')
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
    document.documentElement.classList.toggle('dark')
  }

  const handleResetConfirmation = () => {
    if (confirmationText.toLowerCase() === 'reset me') {
      // Add actual reset logic here
      console.log('Resetting database...')
      setIsDialogOpen(false)
      setConfirmationText('')
    }
  }

  return (
    <div className="space-y-8">
      {/* Dark Mode Toggle */}
      <div className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
        <div>
          <h3 className="text-lg font-medium dark:text-gray-100">Theme</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Switch between light and dark mode
          </p>
        </div>
        <Button
          variant="outline"
          onClick={toggleDarkMode}
          className="dark:bg-gray-700 dark:text-gray-100"
        >
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </Button>
      </div>

      {/* Reset History Section */}
      <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg shadow">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-red-700 dark:text-red-300">
              Danger Zone
            </h3>
            <p className="text-sm text-red-600 dark:text-red-400">
              This will permanently delete all your progress and history
            </p>
          </div>
          
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="destructive">Reset History</Button>
            </DialogTrigger>
            
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Confirm Reset</DialogTitle>
                <DialogDescription>
                  This action cannot be undone. Type "reset me" to confirm.
                </DialogDescription>
              </DialogHeader>
              
              <input
                type="text"
                value={confirmationText}
                onChange={(e) => setConfirmationText(e.target.value)}
                className="border rounded p-2 w-full dark:bg-gray-800 dark:border-gray-700"
                placeholder="Type 'reset me' here"
              />
              
              <DialogFooter>
                <Button
                  variant="destructive"
                  onClick={handleResetConfirmation}
                  disabled={confirmationText.toLowerCase() !== 'reset me'}
                >
                  Confirm Reset
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>
  )
}