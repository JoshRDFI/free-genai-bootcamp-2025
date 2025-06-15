import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  CircularProgress,
  Alert,
  Select,
  MenuItem,
  InputLabel,
  SelectChangeEvent,
  Chip,
} from '@mui/material';
import { api, useWordGroups, useUserProgress } from '../services/api';

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
  review_items: any[];
}

export const Quiz: React.FC = () => {
  console.log('Quiz component rendering');
  const navigate = useNavigate();
  const { groupId } = useParams();
  console.log('URL groupId:', groupId);
  const { wordGroups, loading: groupsLoading, error: groupsError } = useWordGroups();
  const { userProgress, loading: progressLoading, error: progressError } = useUserProgress();
  console.log('Word Groups:', wordGroups);
  console.log('Groups Loading:', groupsLoading);
  console.log('Groups Error:', groupsError);
  const [selectedGroupId, setSelectedGroupId] = useState<string>(groupId || '');
  const [session, setSession] = useState<QuizSession | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (groupId === 'select') {
      // If we're in select mode, don't try to start a quiz
      return;
    }

    if (!groupId) {
      // Don't set error for initial state
      return;
    }

    if (groupId && !selectedGroupId) {
      console.log('Starting quiz with groupId from URL:', groupId);
      setSelectedGroupId(groupId);
      startQuiz();
    }
  }, [groupId]);

  const startQuiz = async () => {
    if (!selectedGroupId) {
      console.log('No group selected, cannot start quiz');
      setError('Please select a word group first');
      return;
    }

    try {
      console.log('Starting quiz with group ID:', selectedGroupId);
      setLoading(true);
      setError(null);
      const response = await api.startQuiz(parseInt(selectedGroupId));
      console.log('Quiz response:', response);
      setSession(response);
    } catch (err) {
      console.error('Quiz start error:', err);
      setError('Failed to start quiz. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSubmit = async () => {
    if (!session || !selectedAnswer) return;

    try {
      const response = await api.submitQuizAnswer(
        session.id,
        session.questions[session.current_question_index].id,
        selectedAnswer
      );

      if (session.current_question_index < session.questions.length - 1) {
        // Move to next question
        setSession({
          ...session,
          current_question_index: session.current_question_index + 1,
        });
        setSelectedAnswer('');
      } else {
        // Quiz completed
        setResult(response);
      }
    } catch (err) {
      console.error('Answer submit error:', err);
      setError('Failed to submit answer. Please try again.');
    }
  };

  const handleSkip = () => {
    if (!session) return;

    if (session.current_question_index < session.questions.length - 1) {
      setSession({
        ...session,
        current_question_index: session.current_question_index + 1,
      });
      setSelectedAnswer('');
    }
  };

  const handleBack = () => {
    if (!session || session.current_question_index === 0) return;

    setSession({
      ...session,
      current_question_index: session.current_question_index - 1,
    });
    setSelectedAnswer('');
  };

  const handleGroupChange = (event: SelectChangeEvent<string>) => {
    const newGroupId = event.target.value;
    setSelectedGroupId(newGroupId);
    if (newGroupId) {
      navigate(`/quiz/${newGroupId}`);
    }
  };

  if (groupsError || progressError) {
    return (
      <Box p={3}>
        <Alert severity="error">
          {groupsError?.message || progressError?.message}
        </Alert>
      </Box>
    );
  }

  if (groupsLoading || progressLoading || loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (groupId === 'select' || !session && !result) {
    return (
      <Box p={3}>
        <Card sx={{ bgcolor: '#f9fafb' }}>
          <CardContent>
            <Typography variant="h4" gutterBottom>
              Vocabulary Quiz
            </Typography>
            <Typography variant="body1" paragraph>
              Test your knowledge of Japanese vocabulary with multiple choice questions.
            </Typography>
            
            <Box mb={2}>
              <Typography variant="subtitle1" gutterBottom>
                Your Current Level:
              </Typography>
              <Chip 
                label={userProgress?.current_level || 'N5'} 
                color="primary" 
                sx={{ fontSize: '1.1rem', padding: '20px 10px' }}
              />
            </Box>
            
            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>Select Word Group</InputLabel>
              <Select
                value={selectedGroupId}
                onChange={handleGroupChange}
                label="Select Word Group"
                sx={{
                  '& .MuiSelect-select': {
                    bgcolor: '#f9fafb',
                    color: '#374151'
                  },
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: '#e5e7eb'
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: '#374151'
                  },
                  '& .MuiSelect-icon': {
                    color: '#374151'
                  }
                }}
                MenuProps={{
                  PaperProps: {
                    sx: {
                      bgcolor: '#f9fafb',
                      '& .MuiMenuItem-root': {
                        color: '#374151',
                        '&:hover': {
                          bgcolor: '#e5e7eb'
                        }
                      }
                    }
                  }
                }}
              >
                
                {wordGroups.map((group) => (
                  <MenuItem key={group.id} value={group.id}>
                    {group.name} ({group.words_count} words)
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}

            <Button
              variant="contained"
              color="primary"
              onClick={startQuiz}
              disabled={!selectedGroupId || loading}
              sx={{ mt: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Start Quiz'}
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
        <Button
          variant="contained"
          color="primary"
          onClick={startQuiz}
          sx={{ mt: 2 }}
        >
          Try Again
        </Button>
      </Box>
    );
  }

  if (result) {
    return (
      <Box p={3}>
        <Card>
          <CardContent>
            <Typography variant="h4" gutterBottom>
              Quiz Completed!
            </Typography>
            <Typography variant="h5" gutterBottom>
              Score: {result.correct_count} / {result.total_questions}
            </Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={() => {
                setSession(null);
                setResult(null);
              }}
              sx={{ mt: 2 }}
            >
              Start New Quiz
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (!session) return null;

  const currentQuestion = session.questions[session.current_question_index];

  return (
    <Box p={3}>
      <Card>
        <CardContent>
          <Typography variant="h5" gutterBottom>
            Question {session.current_question_index + 1} of {session.questions.length}
          </Typography>
          <Typography variant="h6" gutterBottom>
            {currentQuestion.question}
          </Typography>

          <FormControl component="fieldset" sx={{ mt: 2 }}>
            <FormLabel component="legend">Select your answer:</FormLabel>
            <RadioGroup
              value={selectedAnswer}
              onChange={(e) => setSelectedAnswer(e.target.value)}
            >
              {currentQuestion.options.map((option, index) => (
                <FormControlLabel
                  key={index}
                  value={option}
                  control={<Radio />}
                  label={option}
                />
              ))}
            </RadioGroup>
          </FormControl>

          <Box display="flex" justifyContent="space-between" mt={3}>
            <Button
              variant="outlined"
              onClick={handleBack}
              disabled={session.current_question_index === 0}
            >
              Back
            </Button>
            <Button
              variant="outlined"
              onClick={handleSkip}
              disabled={session.current_question_index === session.questions.length - 1}
            >
              Skip
            </Button>
            <Button
              variant="contained"
              color="primary"
              onClick={handleAnswerSubmit}
              disabled={!selectedAnswer}
            >
              Submit
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}; 