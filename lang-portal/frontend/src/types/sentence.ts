export interface SentencePart {
    id: string;
    text: string;
    type: string;
    is_required: boolean;
    position_hint: string;
    grammar_notes: string;
}

export interface Sentence {
    id: string;
    jlpt_level: string;
    category: string;
    source_language: {
        text: string;
        language: string;
        grammar_points: string[];
        key_vocabulary: string[];
        notes: string;
    };
    target_language: {
        text: string;
        language: string;
        grammar_points: string[];
        key_vocabulary: string[];
        notes: string;
    };
    sentence_parts: {
        components: SentencePart[];
        correct_order: string[];
        alternative_orders: {
            order: string[];
            is_grammatically_correct: boolean;
            explanation: string;
        }[];
    };
    exercises: {
        type: string;
        question: string;
        options: string[];
        correct_answer: string;
        hints: string[];
        difficulty_adjustments: {
            easier: string;
            harder: string;
        };
    }[];
    metadata: {
        created_at: string;
        last_modified: string;
        tags: string[];
        usage_count: number;
        success_rate: number;
    };
}

export interface SentenceProgress {
    sentence_id: string;
    attempts: number;
    correct_attempts: number;
    last_attempted: string;
    success_rate: number;
} 