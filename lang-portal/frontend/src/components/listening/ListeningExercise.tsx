import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import AudioPlayer from 'react-h5-audio-player';
import 'react-h5-audio-player/lib/styles.css';
import { ListeningExercise as Exercise, UserAnswer } from '../../types/listening';
import { listeningService } from '../../services/listeningService';
import { Box, Typography, Paper, Button, CircularProgress, Alert, Card, CardContent } from '@mui/material';

const ListeningExercise: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [exercise, setExercise] = useState<Exercise | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState<Record<number, string>>({});
    const [submitted, setSubmitted] = useState(false);
    const [score, setScore] = useState<number | null>(null);

    useEffect(() => {
        const fetchExercise = async () => {
            try {
                const data = await listeningService.getExercise(parseInt(id!));
                console.log('Fetched exercise:', data);
                setExercise(data);
                // Initialize answers state with empty strings for each question
                const initialAnswers: { [key: number]: string } = {};
                data.questions.forEach(q => {
                    initialAnswers[q.id] = '';
                });
                setAnswers(initialAnswers);
            } catch (err) {
                console.error('Error fetching exercise:', err);
                setError('Failed to load exercise');
            } finally {
                setLoading(false);
            }
        };

        if (id) {
            fetchExercise();
        }
    }, [id]);

    const handleAnswerChange = (questionId: number, answer: string) => {
        console.log('Setting answer for question', questionId, 'to', answer);
        setAnswers(prev => {
            const newAnswers = { ...prev };
            newAnswers[questionId] = answer;
            console.log('New answers state:', newAnswers);
            return newAnswers;
        });
    };

    const handleNext = async () => {
        if (!exercise) return;

        const currentQuestion = exercise.questions[currentQuestionIndex];
        console.log('Current question:', currentQuestion);
        
        // If this is the last question, submit all answers
        if (currentQuestionIndex === exercise.questions.length - 1) {
            try {
                // Ensure we have answers for all questions
                const allQuestionsAnswered = exercise.questions.every(q => {
                    const hasAnswer = answers[q.id] && answers[q.id].trim() !== '';
                    console.log(`Question ${q.id} has answer:`, hasAnswer, answers[q.id]);
                    return hasAnswer;
                });

                if (!allQuestionsAnswered) {
                    setError('Please answer all questions before submitting');
                    return;
                }

                // Create answers array in the exact format expected by the API
                const answersArray: UserAnswer[] = exercise.questions.map(q => {
                    const answer = {
                        question_id: q.id,
                        answer: answers[q.id].trim()
                    };
                    console.log('Creating answer object:', answer);
                    return answer;
                });

                console.log('Exercise questions:', exercise.questions);
                console.log('Current answers state:', answers);
                console.log('Submitting answers array:', answersArray);

                const result = await listeningService.submitAnswers(parseInt(id!), answersArray);
                setScore(result.score);
                setSubmitted(true);
            } catch (err: any) {
                console.error('Submission error:', err);
                if (err.response) {
                    console.error('Error response:', err.response.data);
                    setError(`Failed to submit answers: ${err.response.data.detail || 'Unknown error'}`);
                } else {
                    setError('Failed to submit answers');
                }
            }
        } else {
            // Move to next question
            setCurrentQuestionIndex(prev => prev + 1);
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box p={3}>
                <Alert severity="error">{error}</Alert>
            </Box>
        );
    }

    if (!exercise) {
        return (
            <Box p={3}>
                <Alert severity="warning">Exercise not found</Alert>
            </Box>
        );
    }

    const currentQuestion = exercise.questions[currentQuestionIndex];
    console.log('Rendering question:', currentQuestion);

    return (
        <Box p={3}>
            <Card sx={{ bgcolor: '#f9fafb', mb: 4 }}>
                <CardContent>
                    <Typography variant="h4" gutterBottom color="#374151">
                        {exercise.title}
                    </Typography>
                    <Typography variant="subtitle1" color="#6b7280" gutterBottom>
                        {exercise.description}
                    </Typography>
                </CardContent>
            </Card>

            <Card sx={{ bgcolor: '#f9fafb', mb: 4 }}>
                <CardContent>
                    <AudioPlayer
                        src={exercise.audio_file}
                        showJumpControls={false}
                        layout="stacked"
                        autoPlay={false}
                        preload="auto"
                        style={{
                            borderRadius: '8px',
                            backgroundColor: '#f9fafb',
                            boxShadow: 'none'
                        }}
                    />
                </CardContent>
            </Card>

            {!submitted ? (
                <Box>
                    <Card sx={{ bgcolor: '#f9fafb', mb: 3 }}>
                        <CardContent>
                            <Typography variant="h6" gutterBottom color="#374151">
                                Question {currentQuestionIndex + 1} of {exercise.questions.length}
                            </Typography>
                            <Typography variant="body1" color="#6b7280" gutterBottom>
                                {currentQuestion.question_text}
                            </Typography>

                            {currentQuestion.question_type === 'multiple_choice' && currentQuestion.options && (
                                <Box sx={{ mt: 2 }}>
                                    {currentQuestion.options.map((option, i) => (
                                        <Button
                                            key={i}
                                            variant={answers[currentQuestion.id] === option ? "contained" : "outlined"}
                                            onClick={() => handleAnswerChange(currentQuestion.id, option)}
                                            sx={{ 
                                                mr: 1, 
                                                mb: 1,
                                                bgcolor: answers[currentQuestion.id] === option ? '#3b82f6' : 'transparent',
                                                color: answers[currentQuestion.id] === option ? 'white' : '#374151',
                                                borderColor: '#e5e7eb',
                                                '&:hover': {
                                                    bgcolor: answers[currentQuestion.id] === option ? '#2563eb' : '#f3f4f6',
                                                    borderColor: '#374151'
                                                }
                                            }}
                                        >
                                            {option}
                                        </Button>
                                    ))}
                                </Box>
                            )}

                            {currentQuestion.question_type === 'fill_blank' && (
                                <Box sx={{ mt: 2 }}>
                                    <input
                                        type="text"
                                        value={answers[currentQuestion.id] || ''}
                                        onChange={(e) => handleAnswerChange(currentQuestion.id, e.target.value)}
                                        style={{ 
                                            width: '100%', 
                                            padding: '8px',
                                            border: '1px solid #e5e7eb',
                                            borderRadius: '4px',
                                            backgroundColor: '#f9fafb',
                                            color: '#374151'
                                        }}
                                    />
                                </Box>
                            )}

                            {currentQuestion.question_type === 'true_false' && (
                                <Box sx={{ mt: 2 }}>
                                    <Button
                                        variant={answers[currentQuestion.id] === 'true' ? "contained" : "outlined"}
                                        onClick={() => handleAnswerChange(currentQuestion.id, 'true')}
                                        sx={{ 
                                            mr: 1,
                                            bgcolor: answers[currentQuestion.id] === 'true' ? '#3b82f6' : 'transparent',
                                            color: answers[currentQuestion.id] === 'true' ? 'white' : '#374151',
                                            borderColor: '#e5e7eb',
                                            '&:hover': {
                                                bgcolor: answers[currentQuestion.id] === 'true' ? '#2563eb' : '#f3f4f6',
                                                borderColor: '#374151'
                                            }
                                        }}
                                    >
                                        True
                                    </Button>
                                    <Button
                                        variant={answers[currentQuestion.id] === 'false' ? "contained" : "outlined"}
                                        onClick={() => handleAnswerChange(currentQuestion.id, 'false')}
                                        sx={{ 
                                            bgcolor: answers[currentQuestion.id] === 'false' ? '#3b82f6' : 'transparent',
                                            color: answers[currentQuestion.id] === 'false' ? 'white' : '#374151',
                                            borderColor: '#e5e7eb',
                                            '&:hover': {
                                                bgcolor: answers[currentQuestion.id] === 'false' ? '#2563eb' : '#f3f4f6',
                                                borderColor: '#374151'
                                            }
                                        }}
                                    >
                                        False
                                    </Button>
                                </Box>
                            )}

                            <Button
                                variant="contained"
                                color="primary"
                                onClick={handleNext}
                                disabled={!answers[currentQuestion.id]}
                                sx={{ 
                                    mt: 2,
                                    bgcolor: '#3b82f6',
                                    '&:hover': {
                                        bgcolor: '#2563eb'
                                    }
                                }}
                            >
                                {currentQuestionIndex === exercise.questions.length - 1 ? 'Submit' : 'Next Question'}
                            </Button>
                        </CardContent>
                    </Card>
                </Box>
            ) : (
                <Card sx={{ bgcolor: '#f9fafb', textAlign: 'center' }}>
                    <CardContent>
                        <Typography variant="h5" gutterBottom color="#374151">
                            Exercise Completed!
                        </Typography>
                        <Typography variant="h6" color="#3b82f6" gutterBottom>
                            Your Score: {score}%
                        </Typography>
                        <Button
                            variant="contained"
                            color="primary"
                            onClick={() => window.location.reload()}
                            sx={{ 
                                mt: 2,
                                bgcolor: '#3b82f6',
                                '&:hover': {
                                    bgcolor: '#2563eb'
                                }
                            }}
                        >
                            Try Again
                        </Button>
                    </CardContent>
                </Card>
            )}
        </Box>
    );
};

export default ListeningExercise; 