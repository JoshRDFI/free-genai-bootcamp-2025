import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ListeningExercise } from '../../types/listening';
import { listeningService } from '../../services/listeningService';
import { Box, Typography, Grid, Card, CardContent, CardActions, Button, CircularProgress, Alert } from '@mui/material';

const ListeningExercisesList: React.FC = () => {
    const [exercises, setExercises] = useState<ListeningExercise[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchExercises = async () => {
            try {
                console.log('Fetching exercises...');
                const data = await listeningService.getExercises();
                console.log('Received exercises:', data);
                setExercises(data);
            } catch (err) {
                console.error('Error fetching exercises:', err);
                if (err instanceof Error) {
                    setError(`Failed to load exercises: ${err.message}`);
                } else {
                    setError('Failed to load exercises');
                }
            } finally {
                setLoading(false);
            }
        };

        fetchExercises();
    }, []);

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
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                    Please check the browser console for more details.
                </Typography>
            </Box>
        );
    }

    return (
        <Box p={3}>
            <Card sx={{ bgcolor: '#f9fafb', mb: 4 }}>
                <CardContent>
                    <Typography variant="h4" gutterBottom>
                        Listening Exercises
                    </Typography>
                    <Typography variant="body1" paragraph>
                        Practice your Japanese listening comprehension with audio exercises.
                    </Typography>
                </CardContent>
            </Card>

            <Grid container spacing={3}>
                {exercises.map((exercise) => (
                    <Grid item xs={12} sm={6} md={4} key={exercise.id}>
                        <Card sx={{ 
                            bgcolor: '#f9fafb',
                            '&:hover': {
                                boxShadow: 3,
                                transform: 'translateY(-2px)',
                                transition: 'all 0.2s ease-in-out'
                            }
                        }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom color="#374151">
                                    {exercise.title}
                                </Typography>
                                <Typography variant="body2" color="#6b7280" gutterBottom>
                                    {exercise.description}
                                </Typography>
                                <Typography variant="body2" color="#6b7280">
                                    Difficulty: {exercise.difficulty}
                                </Typography>
                            </CardContent>
                            <CardActions>
                                <Button
                                    component={Link}
                                    to={`/listening/${exercise.id}`}
                                    variant="contained"
                                    color="primary"
                                    fullWidth
                                    sx={{
                                        bgcolor: '#3b82f6',
                                        '&:hover': {
                                            bgcolor: '#2563eb'
                                        }
                                    }}
                                >
                                    Start Exercise
                                </Button>
                            </CardActions>
                        </Card>
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
};

export default ListeningExercisesList; 