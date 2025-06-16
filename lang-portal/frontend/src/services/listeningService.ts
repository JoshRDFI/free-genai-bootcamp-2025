import axios from 'axios';
import { ListeningExercise, ListeningAttempt, UserAnswer } from '../types/listening';

const API_URL = 'http://localhost:5000/api';

export const listeningService = {
    // Get all listening exercises
    getExercises: async (): Promise<ListeningExercise[]> => {
        const response = await axios.get(`${API_URL}/listening/exercises`);
        return response.data;
    },

    // Get a specific exercise by ID
    getExercise: async (id: number): Promise<ListeningExercise> => {
        const response = await axios.get(`${API_URL}/listening/exercises/${id}`);
        return response.data;
    },

    // Submit answers for an exercise
    submitAnswers: async (exerciseId: number, answers: UserAnswer[]): Promise<ListeningAttempt> => {
        const response = await axios.post(`${API_URL}/listening/exercises/${exerciseId}/submit`, answers);
        return response.data;
    },

    // Get user's attempts for an exercise
    getAttempts: async (exerciseId: number): Promise<ListeningAttempt[]> => {
        const response = await axios.get(`${API_URL}/listening/exercises/${exerciseId}/attempts`);
        return response.data;
    }
}; 