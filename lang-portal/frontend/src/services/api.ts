import { useState, useEffect } from 'react';
import axios from 'axios';

const useWords = (groupId?: number) => {
  const [words, setWords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    const fetchWords = async () => {
      try {
        const response = await axios.get('/api/words', {
          params: {
            page,
            group_id: groupId,
          },
        });
        setWords(response.data.words);
        setTotalPages(response.data.totalPages);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchWords();
  }, [groupId, page]);

  return { words, loading, error, page, setPage, totalPages };
};

const useWordGroups = () => {
  const [wordGroups, setWordGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    const fetchWordGroups = async () => {
      try {
        const response = await axios.get('/api/groups', {
          params: {
            page,
          },
        });
        setWordGroups(response.data.groups);
        setTotalPages(response.data.totalPages);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchWordGroups();
  }, [page]);

  return { wordGroups, loading, error, page, setPage, totalPages };
};

const useStudyActivities = () => {
  const [studyActivities, setStudyActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStudyActivities = async () => {
      try {
        const response = await axios.get('/api/study_activities');
        setStudyActivities(response.data.studyActivities);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchStudyActivities();
  }, []);

  return { studyActivities, loading, error };
};

const useStudyActivity = (id: string) => {
  const [studyActivity, setStudyActivity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStudyActivity = async () => {
      try {
        const response = await axios.get(`/api/study_activities/${id}`);
        setStudyActivity(response.data.studyActivity);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchStudyActivity();
    }
  }, [id]);

  return { studyActivity, loading, error };
};

const useSessions = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const response = await axios.get('/api/sessions', {
          params: {
            page,
          },
        });
        setSessions(response.data.sessions);
        setTotalPages(response.data.totalPages);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchSessions();
  }, [page]);

  return { sessions, loading, error, page, setPage, totalPages };
};

const useSession = (id: string) => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const response = await axios.get(`/api/sessions/${id}`);
        setSession(response.data.session);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchSession();
    }
  }, [id]);

  return { session, loading, error };
};

const useWord = (id: string) => {
  const [word, setWord] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchWord = async () => {
      try {
        const response = await axios.get(`/api/words/${id}`);
        setWord(response.data.word);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchWord();
    }
  }, [id]);

  return { word, loading, error };
};

const useWordGroup = (id: string) => {
  const [wordGroup, setWordGroup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchWordGroup = async () => {
      try {
        const response = await axios.get(`/api/groups/${id}`);
        setWordGroup(response.data.wordGroup);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchWordGroup();
    }
  }, [id]);

  return { wordGroup, loading, error };
};

export {
  useWords,
  useWordGroups,
  useStudyActivities,
  useStudyActivity,
  useSessions,
  useSession,
  useWord,
  useWordGroup,
};