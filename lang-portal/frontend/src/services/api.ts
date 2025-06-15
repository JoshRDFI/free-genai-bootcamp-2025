import { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';
console.log('API Base URL:', API_BASE_URL);

interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_items: number;
    items_per_page: number;
  };
}

interface Word {
  id: number;
  kanji: string;
  romaji: string;
  english: string;
  parts: Record<string, any>;
  correct_count: number;
  wrong_count: number;
}

interface Group {
  id: number;
  name: string;
  words_count: number;
}

interface StudyActivity {
  id: number;
  name: string;
  description: string;
  thumbnail: string;
  url: string;
  sessions?: StudySession[];
}

interface StudySession {
  id: number;
  group_id: number;
  study_activity_id: number;
  created_at: string;
  updated_at: string;
  group: Group;
  study_activity: StudyActivity;
  review_items: WordReviewItem[];
}

interface WordReviewItem {
  id: number;
  word_id: number;
  study_session_id: number;
  correct: boolean;
  created_at: string;
  word: Word;
  session: StudySession;
}

interface QuizQuestion {
  id: number;
  word_id: number;
  question_type: string;
  question: string;
  correct_answer: string;
  options: string[];
}

interface QuizSession {
  id: number;
  questions: QuizQuestion[];
  current_question_index: number;
  completed: boolean;
}

interface QuizResult {
  correct_count: number;
  total_questions: number;
  review_items: WordReviewItem[];
}

interface UserProgress {
  id: number;
  current_level: string;
  created_at: string;
  updated_at: string;
}

export const useWords = (groupId?: number, initialPage = 1) => {
  const [words, setWords] = useState<Word[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(initialPage);

  useEffect(() => {
    const fetchWords = async () => {
      try {
        setLoading(true);
        const response = await axios.get<PaginatedResponse<Word>>(`${API_BASE_URL}/words`, {
          params: { page, group_id: groupId }
        });
        setWords(response.data.items);
        setTotalPages(response.data.pagination.total_pages);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch words'));
      } finally {
        setLoading(false);
      }
    };

    fetchWords();
  }, [page, groupId]);

  return { words, loading, error, totalPages, page, setPage };
};

export const useWordGroups = (initialPage = 1) => {
  const [wordGroups, setWordGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(initialPage);

  useEffect(() => {
    const fetchWordGroups = async () => {
      try {
        setLoading(true);
        console.log('Fetching word groups from:', `${API_BASE_URL}/groups`);
        const response = await axios.get<PaginatedResponse<Group>>(`${API_BASE_URL}/groups`, {
          params: { page }
        });
        console.log('Word groups response:', response.data);
        if (response.data && response.data.items) {
          setWordGroups(response.data.items);
          setTotalPages(response.data.pagination.total_pages);
        } else {
          console.error('Invalid response format:', response.data);
          setError(new Error('Invalid response format from server'));
        }
        setError(null);
      } catch (err) {
        console.error('Error fetching word groups:', err);
        if (axios.isAxiosError(err)) {
          console.error('Axios error details:', {
            status: err.response?.status,
            statusText: err.response?.statusText,
            data: err.response?.data
          });
        }
        setError(err instanceof Error ? err : new Error('Failed to fetch word groups'));
      } finally {
        setLoading(false);
      }
    };

    fetchWordGroups();
  }, [page]);

  return { wordGroups, loading, error, totalPages, page, setPage };
};

export const useStudyActivities = () => {
  const [studyActivities, setStudyActivities] = useState<StudyActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchStudyActivities = async () => {
      try {
        setLoading(true);
        const response = await axios.get<StudyActivity[]>(`${API_BASE_URL}/study-activities`);
        setStudyActivities(response.data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch study activities'));
      } finally {
        setLoading(false);
      }
    };

    fetchStudyActivities();
  }, []);

  return { studyActivities, loading, error };
};

export const useStudyActivity = (id: string | undefined) => {
  const [studyActivity, setStudyActivity] = useState<StudyActivity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchStudyActivity = async () => {
      if (!id) return;
      try {
        setLoading(true);
        const response = await axios.get<StudyActivity>(`${API_BASE_URL}/study-activities/${id}`);
        setStudyActivity(response.data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch study activity'));
      } finally {
        setLoading(false);
      }
    };

    fetchStudyActivity();
  }, [id]);

  return { studyActivity, loading, error };
};

export const useSessions = (initialPage = 1) => {
  const [sessions, setSessions] = useState<StudySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(initialPage);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        setLoading(true);
        const response = await axios.get<PaginatedResponse<StudySession>>(`${API_BASE_URL}/sessions`, {
          params: { page }
        });
        setSessions(response.data.items);
        setTotalPages(response.data.pagination.total_pages);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch sessions'));
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
  }, [page]);

  return { sessions, loading, error, totalPages, page, setPage };
};

export const useUserProgress = () => {
  const [userProgress, setUserProgress] = useState<UserProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchUserProgress = async () => {
      try {
        setLoading(true);
        const response = await axios.get<UserProgress>(`${API_BASE_URL}/user-progress`);
        setUserProgress(response.data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch user progress'));
      } finally {
        setLoading(false);
      }
    };

    fetchUserProgress();
  }, []);

  const updateUserProgress = async (level: string) => {
    try {
      setLoading(true);
      const response = await axios.put<UserProgress>(`${API_BASE_URL}/user-progress`, { level });
      setUserProgress(response.data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to update user progress'));
    } finally {
      setLoading(false);
    }
  };

  return { userProgress, loading, error, updateUserProgress };
};

export const useGroup = (groupId: string | undefined) => {
  const [group, setGroup] = useState<Group | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchGroup = async () => {
      if (!groupId) return;
      try {
        setLoading(true);
        const response = await axios.get<Group>(`${API_BASE_URL}/groups/${groupId}`);
        setGroup(response.data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch group'));
      } finally {
        setLoading(false);
      }
    };

    fetchGroup();
  }, [groupId]);

  return { group, loading, error };
};

export const api = {
  // Study Activities
  getStudyActivities: () => 
    axios.get(`${API_BASE_URL}/study-activities`).then(res => res.data),

  getStudyActivity: (id: number) =>
    axios.get(`${API_BASE_URL}/study-activities/${id}`).then(res => res.data),

  // Words
  getWords: (page = 1, sortBy = 'kanji', order = 'asc') =>
    axios.get(`${API_BASE_URL}/words`, {
      params: { page, sort_by: sortBy, order }
    }).then(res => res.data),

  // Groups
  getGroups: (page = 1, sortBy = 'name', order = 'asc') =>
    axios.get(`${API_BASE_URL}/groups`, {
      params: { page, sort_by: sortBy, order }
    }).then(res => res.data),

  getGroup: (id: number) =>
    axios.get(`${API_BASE_URL}/groups/${id}`).then(res => res.data),

  // Study Sessions
  getSessions: (page = 1) =>
    axios.get(`${API_BASE_URL}/sessions`, {
      params: { page }
    }).then(res => res.data),

  createStudySession: (groupId: number, studyActivityId: number) =>
    axios.post(`${API_BASE_URL}/study_sessions`, {
      group_id: groupId,
      study_activity_id: studyActivityId
    }).then(res => res.data),

  logReview: (sessionId: number, wordId: number, correct: boolean) =>
    axios.post(`${API_BASE_URL}/study_sessions/${sessionId}/review`, {
      word_id: wordId,
      correct
    }).then(res => res.data),

  // Quiz
  startQuiz: (groupId: number) =>
    axios.post(`${API_BASE_URL}/quiz/start`, {
      group_id: groupId
    }).then(res => res.data),

  submitQuizAnswer: (sessionId: number, questionId: number, selectedAnswer: string) =>
    axios.post(`${API_BASE_URL}/quiz/${sessionId}/submit`, {
      question_id: questionId,
      selected_answer: selectedAnswer
    }).then(res => res.data)
}; 