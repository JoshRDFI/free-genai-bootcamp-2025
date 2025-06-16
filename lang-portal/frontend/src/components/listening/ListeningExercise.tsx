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
    const [answers, setAnswers] = useState<UserAnswer[]>([]);
    const [submitted, setSubmitted] = useState(false);
    const [score, setScore] = useState<number | null>(null);

    useEffect(() => {
        const fetchExercise = async () => {
            try {
                if (!id) return;
                const data = await listeningService.getExercise(parseInt(id));
                setExercise(data);
                setAnswers(data.questions.map(q => ({ question_id: q.id, answer: '' })));
            } catch (err) {
                setError('Failed to load exercise');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchExercise();
    }, [id]);

    const handleAnswerChange = (questionId: number, answer: string) => {
        setAnswers(prev => prev.map(a => 
            a.question_id === questionId ? { ...a, answer } : a
        ));
    };

    const handleSubmit = async () => {
        try {
            if (!id) return;
            const result = await listeningService.submitAnswers(parseInt(id), answers);
            setScore(result.score);
            setSubmitted(true);
        } catch (err) {
            setError('Failed to submit answers');
            console.error(err);
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
                        src={`/audio/${exercise.audio_file}`}
                        showJumpControls={false}
                        layout="stacked"
                    />
                </CardContent>
            </Card>

            {!submitted ? (
                <Box>
                    {exercise.questions.map((question, index) => (
                        <Card key={question.id} sx={{ bgcolor: '#f9fafb', mb: 3 }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom color="#374151">
                                    Question {index + 1}
                                </Typography>
                                <Typography variant="body1" color="#6b7280" gutterBottom>
                                    {question.question_text}
                                </Typography>

                                {question.question_type === 'multiple_choice' && question.options && (
                                    <Box sx={{ mt: 2 }}>
                                        {question.options.map((option, i) => (
                                            <Button
                                                key={i}
                                                variant={answers.find(a => a.question_id === question.id)?.answer === option ? "contained" : "outlined"}
                                                onClick={() => handleAnswerChange(question.id, option)}
                                                sx={{ 
                                                    mr: 1, 
                                                    mb: 1,
                                                    bgcolor: answers.find(a => a.question_id === question.id)?.answer === option ? '#3b82f6' : 'transparent',
                                                    color: answers.find(a => a.question_id === question.id)?.answer === option ? 'white' : '#374151',
                                                    borderColor: '#e5e7eb',
                                                    '&:hover': {
                                                        bgcolor: answers.find(a => a.question_id === question.id)?.answer === option ? '#2563eb' : '#f3f4f6',
                                                        borderColor: '#374151'
                                                    }
                                                }}
                                            >
                                                {option}
                                            </Button>
                                        ))}
                                    </Box>
                                )}

                                {question.question_type === 'fill_blank' && (
                                    <Box sx={{ mt: 2 }}>
                                        <input
                                            type="text"
                                            value={answers.find(a => a.question_id === question.id)?.answer || ''}
                                            onChange={(e) => handleAnswerChange(question.id, e.target.value)}
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

                                {question.question_type === 'true_false' && (
                                    <Box sx={{ mt: 2 }}>
                                        <Button
                                            variant={answers.find(a => a.question_id === question.id)?.answer === 'true' ? "contained" : "outlined"}
                                            onClick={() => handleAnswerChange(question.id, 'true')}
                                            sx={{ 
                                                mr: 1,
                                                bgcolor: answers.find(a => a.question_id === question.id)?.answer === 'true' ? '#3b82f6' : 'transparent',
                                                color: answers.find(a => a.question_id === question.id)?.answer === 'true' ? 'white' : '#374151',
                                                borderColor: '#e5e7eb',
                                                '&:hover': {
                                                    bgcolor: answers.find(a => a.question_id === question.id)?.answer === 'true' ? '#2563eb' : '#f3f4f6',
                                                    borderColor: '#374151'
                                                }
                                            }}
                                        >
                                            True
                                        </Button>
                                        <Button
                                            variant={answers.find(a => a.question_id === question.id)?.answer === 'false' ? "contained" : "outlined"}
                                            onClick={() => handleAnswerChange(question.id, 'false')}
                                            sx={{ 
                                                bgcolor: answers.find(a => a.question_id === question.id)?.answer === 'false' ? '#3b82f6' : 'transparent',
                                                color: answers.find(a => a.question_id === question.id)?.answer === 'false' ? 'white' : '#374151',
                                                borderColor: '#e5e7eb',
                                                '&:hover': {
                                                    bgcolor: answers.find(a => a.question_id === question.id)?.answer === 'false' ? '#2563eb' : '#f3f4f6',
                                                    borderColor: '#374151'
                                                }
                                            }}
                                        >
                                            False
                                        </Button>
                                    </Box>
                                )}
                            </CardContent>
                        </Card>
                    ))}

                    <Button
                        variant="contained"
                        color="primary"
                        onClick={handleSubmit}
                        disabled={answers.some(a => !a.answer)}
                        sx={{ 
                            mt: 2,
                            bgcolor: '#3b82f6',
                            '&:hover': {
                                bgcolor: '#2563eb'
                            }
                        }}
                    >
                        Submit Answers
                    </Button>
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