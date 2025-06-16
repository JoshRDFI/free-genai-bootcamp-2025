export type QuestionType = 'multiple_choice' | 'fill_blank' | 'true_false';

export interface ListeningQuestion {
    id: number;
    exercise_id: number;
    question_type: QuestionType;
    question_text: string;
    correct_answer: string;
    options?: string[];  // For multiple choice questions
    points: number;
}

export interface ListeningExercise {
    id: number;
    title: string;
    audio_file: string;
    difficulty: string;
    description: string;
    created_at: string;
    questions: ListeningQuestion[];
}

export interface ListeningAttempt {
    id: number;
    exercise_id: number;
    user_id: number;
    score: number;
    completed_at: string;
    answers: {
        question_id: number;
        answer: string;
        is_correct: boolean;
    }[];
}

export interface UserAnswer {
    question_id: number;
    answer: string;
} 