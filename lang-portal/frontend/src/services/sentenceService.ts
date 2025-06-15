import { Sentence, SentenceProgress } from '../types/sentence';

const API_BASE_URL = 'http://localhost:5000/api';

export const sentenceService = {
    async getSentences(): Promise<Sentence[]> {
        const response = await fetch(`${API_BASE_URL}/sentences`);
        if (!response.ok) {
            throw new Error('Failed to fetch sentences');
        }
        return response.json();
    },

    async submitSentenceAttempt(
        sentenceId: string,
        constructedSentence: string,
        timeTaken: number
    ): Promise<SentenceProgress> {
        const response = await fetch(`${API_BASE_URL}/sentences/attempt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sentence_id: sentenceId,
                constructed_sentence: constructedSentence,
                time_taken: timeTaken,
                is_correct: false  // This will be updated by the backend
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to submit sentence attempt');
        }

        return response.json();
    },
}; 