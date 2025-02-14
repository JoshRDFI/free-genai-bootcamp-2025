// Recommended location for shared types
export interface Session {
    id: number
    activity: string
    duration: number
    date: Date
    accuracy: number
    groupId: number
    wordReviews: {
      wordId: number
      correct: boolean
    }[]
  }