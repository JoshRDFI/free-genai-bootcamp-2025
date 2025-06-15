import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

export const api = {
  // Study Activities
  getStudyActivities: () => 
    axios.get(`${API_BASE_URL}/study-activities`).then(res => res.data),

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