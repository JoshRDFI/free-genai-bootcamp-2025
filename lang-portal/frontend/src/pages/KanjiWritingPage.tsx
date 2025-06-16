import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Select,
  MenuItem,
  InputLabel,
  FormControl,
  SelectChangeEvent,
  Chip,
} from '@mui/material';
import { useUserProgress } from '../services/api';
import wordsData from '@/data/words.json';

interface Point {
  x: number;
  y: number;
}

interface Stroke {
  points: Point[];
  isCorrect: boolean;
}

interface StrokeData {
  strokes: number;
  strokeOrder: Array<{
    points: Array<[number, number]>;
  }>;
}

interface Word {
  kanji: string;
  romaji: string;
  english: string;
  level: string;
  group_id: number;
  category: string;
  parts?: StrokeData;
}

// Sample stroke data for some common kanji
const STROKE_DATA: Record<string, StrokeData> = {
  "一": {
    "strokes": 1,
    "strokeOrder": [
      {"points": [[0.2, 0.5], [0.8, 0.5]]}
    ]
  },
  "二": {
    "strokes": 2,
    "strokeOrder": [
      {"points": [[0.2, 0.3], [0.8, 0.3]]},
      {"points": [[0.2, 0.7], [0.8, 0.7]]}
    ]
  },
  "三": {
    "strokes": 3,
    "strokeOrder": [
      {"points": [[0.2, 0.2], [0.8, 0.2]]},
      {"points": [[0.2, 0.5], [0.8, 0.5]]},
      {"points": [[0.2, 0.8], [0.8, 0.8]]}
    ]
  },
  "四": {
    "strokes": 5,
    "strokeOrder": [
      {"points": [[0.2, 0.2], [0.8, 0.2]]},
      {"points": [[0.2, 0.2], [0.2, 0.8]]},
      {"points": [[0.2, 0.8], [0.8, 0.8]]},
      {"points": [[0.8, 0.2], [0.8, 0.8]]},
      {"points": [[0.3, 0.5], [0.7, 0.5]]}
    ]
  },
  "五": {
    "strokes": 4,
    "strokeOrder": [
      {"points": [[0.2, 0.2], [0.8, 0.2]]},
      {"points": [[0.2, 0.2], [0.2, 0.8]]},
      {"points": [[0.2, 0.8], [0.8, 0.8]]},
      {"points": [[0.3, 0.5], [0.7, 0.5]]}
    ]
  }
};

const KanjiWritingPage: React.FC = () => {
  const navigate = useNavigate();
  const { groupId } = useParams<{ groupId: string }>();
  const { userProgress, loading: progressLoading, error: progressError } = useUserProgress();
  const [selectedGroupId, setSelectedGroupId] = useState<string>(groupId || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [currentWord, setCurrentWord] = useState<Word | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentStroke, setCurrentStroke] = useState<number>(0);
  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const [feedback, setFeedback] = useState<string>('');
  const [words, setWords] = useState<Word[]>([]);
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [score, setScore] = useState(0);
  const [showGuide, setShowGuide] = useState(true);
  const [animationFrame, setAnimationFrame] = useState(0);

  // Get unique word groups for the dropdown
  const wordGroups = React.useMemo(() => {
    const groups = new Map<number, { id: number; category: string }>();
    const userLevel = userProgress?.current_level || 'N5';
    
    // Convert level to number for comparison (N5 = 5, N4 = 4, etc.)
    const userLevelNum = parseInt(userLevel.replace('N', ''));
    
    wordsData.forEach(word => {
      // Convert word level to number for comparison
      const wordLevelNum = parseInt(word.level.replace('N', ''));
      
      // Only include groups up to user's current level
      if (wordLevelNum >= userLevelNum && !groups.has(word.group_id)) {
        groups.set(word.group_id, {
          id: word.group_id,
          category: word.category
        });
      }
    });
    return Array.from(groups.values()).sort((a, b) => a.id - b.id);
  }, [userProgress?.current_level]);

  useEffect(() => {
    if (!groupId || groupId === 'select') return;
    
    try {
      setLoading(true);
      const numericGroupId = parseInt(groupId, 10);
      if (isNaN(numericGroupId)) {
        throw new Error('Invalid group ID');
      }

      // Get words for this group from the local data
      const groupWords = wordsData.filter(word => word.group_id === numericGroupId);
      if (groupWords.length === 0) {
        throw new Error('No words found in this group');
      }

      // Add stroke data to words
      const wordsWithStrokeData = groupWords.map(word => ({
        ...word,
        parts: STROKE_DATA[word.kanji] || {
          strokes: 0,
          strokeOrder: []
        }
      }));

      setWords(wordsWithStrokeData);
      setCurrentWord(wordsWithStrokeData[0]);
      setStrokes([]);
      setCurrentStroke(0);
      setCurrentWordIndex(0);
      setScore(0);
    } catch (error) {
      console.error('Failed to load words:', error);
      setError(error instanceof Error ? error.message : 'Failed to load words. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [groupId]);

  useEffect(() => {
    if (!canvasRef.current || !currentWord) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    for (let i = 0; i < 3; i++) {
      ctx.beginPath();
      ctx.moveTo(canvas.width / 3 * (i + 1), 0);
      ctx.lineTo(canvas.width / 3 * (i + 1), canvas.height);
      ctx.stroke();
      
      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 3 * (i + 1));
      ctx.lineTo(canvas.width, canvas.height / 3 * (i + 1));
      ctx.stroke();
    }

    // Draw reference kanji (faded)
    ctx.font = '48px sans-serif';
    ctx.fillStyle = 'rgba(0, 0, 0, 0.1)';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(currentWord.kanji, canvas.width / 2, canvas.height / 2);

    // Draw completed strokes
    strokes.forEach((stroke, index) => {
      if (stroke.points.length < 2) return;
      
      ctx.beginPath();
      ctx.moveTo(stroke.points[0].x, stroke.points[0].y);
      stroke.points.forEach(point => {
        ctx.lineTo(point.x, point.y);
      });
      ctx.strokeStyle = stroke.isCorrect ? '#10B981' : '#EF4444';
      ctx.lineWidth = 3;
      ctx.stroke();
    });

    // Draw current stroke guide if enabled
    if (showGuide && currentWord.parts?.strokeOrder && currentWord.parts.strokeOrder[currentStroke]) {
      const guideStroke = currentWord.parts.strokeOrder[currentStroke];
      const startPoint = guideStroke.points[0];
      const endPoint = guideStroke.points[1];
      
      // Animate the guide stroke
      const progress = (Math.sin(Date.now() / 500) + 1) / 2;
      const currentX = startPoint[0] + (endPoint[0] - startPoint[0]) * progress;
      const currentY = startPoint[1] + (endPoint[1] - startPoint[1]) * progress;
      
      ctx.beginPath();
      ctx.moveTo(startPoint[0] * canvas.width, startPoint[1] * canvas.height);
      ctx.lineTo(currentX * canvas.width, currentY * canvas.height);
      ctx.strokeStyle = 'rgba(59, 130, 246, 0.5)';
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  }, [currentWord, strokes, currentStroke, showGuide, animationFrame]);

  // Animation loop for guide stroke
  useEffect(() => {
    if (showGuide && currentWord) {
      const animationId = requestAnimationFrame(() => {
        setAnimationFrame(prev => prev + 1);
      });
      return () => cancelAnimationFrame(animationId);
    }
  }, [showGuide, animationFrame, currentWord]);

  const getCanvasPoint = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>): Point => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    
    return {
      x: clientX - rect.left,
      y: clientY - rect.top
    };
  };

  const startDrawing = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current || !currentWord) return;
    
    const point = getCanvasPoint(e);
    setIsDrawing(true);
    setStrokes(prev => [...prev, { points: [point], isCorrect: false }]);
  };

  const draw = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !canvasRef.current || !currentWord) return;
    
    const point = getCanvasPoint(e);
    setStrokes(prev => {
      const newStrokes = [...prev];
      const currentStroke = newStrokes[newStrokes.length - 1];
      currentStroke.points.push(point);
      return newStrokes;
    });
  };

  const stopDrawing = () => {
    if (!isDrawing || !currentWord) return;
    
    setIsDrawing(false);
    validateStroke();
  };

  const validateStroke = () => {
    if (!currentWord || !currentWord.parts?.strokeOrder) return;

    const currentStrokeData = currentWord.parts.strokeOrder[currentStroke];
    if (!currentStrokeData) return;

    const drawnStroke = strokes[strokes.length - 1];
    const startPoint = currentStrokeData.points[0];
    const endPoint = currentStrokeData.points[1];

    // Calculate the angle and length of both strokes
    const drawnVector = {
      x: drawnStroke.points[drawnStroke.points.length - 1].x - drawnStroke.points[0].x,
      y: drawnStroke.points[drawnStroke.points.length - 1].y - drawnStroke.points[0].y
    };
    const correctVector = {
      x: (endPoint[0] - startPoint[0]) * canvasRef.current!.width,
      y: (endPoint[1] - startPoint[1]) * canvasRef.current!.height
    };

    const drawnLength = Math.sqrt(drawnVector.x * drawnVector.x + drawnVector.y * drawnVector.y);
    const correctLength = Math.sqrt(correctVector.x * correctVector.x + correctVector.y * correctVector.y);
    const lengthRatio = Math.min(drawnLength, correctLength) / Math.max(drawnLength, correctLength);

    const drawnAngle = Math.atan2(drawnVector.y, drawnVector.x);
    const correctAngle = Math.atan2(correctVector.y, correctVector.x);
    const angleDiff = Math.abs(drawnAngle - correctAngle);

    // Consider the stroke correct if the angle difference is less than 45 degrees
    // and the length ratio is greater than 0.7
    const isCorrect = angleDiff < Math.PI / 4 && lengthRatio > 0.7;

    setStrokes(prev => {
      const newStrokes = [...prev];
      newStrokes[newStrokes.length - 1].isCorrect = isCorrect;
      return newStrokes;
    });

    if (isCorrect) {
      setCurrentStroke(prev => prev + 1);
      setScore(prev => prev + 1);
      setFeedback('Correct stroke!');
    } else {
      setFeedback('Try again!');
    }

    // Check if all strokes are complete
    if (currentWord.parts.strokeOrder && currentStroke + 1 === currentWord.parts.strokeOrder.length) {
      setFeedback('Great job! Move to next kanji.');
    }
  };

  const nextWord = () => {
    if (currentWordIndex < words.length - 1) {
      setCurrentWordIndex(prev => prev + 1);
      setCurrentWord(words[currentWordIndex + 1]);
      setCurrentStroke(0);
      setStrokes([]);
      setFeedback('');
    }
  };

  const clearCanvas = () => {
    if (!canvasRef.current) return;
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    setCurrentStroke(0);
    setStrokes([]);
  };

  if (progressError) {
    return (
      <Box p={3}>
        <Alert severity="error">
          {progressError?.message}
        </Alert>
      </Box>
    );
  }

  if (progressLoading || loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (groupId === 'select' || !selectedGroupId) {
    return (
      <Box p={3}>
        <Card sx={{ bgcolor: '#f9fafb' }}>
          <CardContent>
            <Typography variant="h4" gutterBottom>
              Kanji Writing Practice
            </Typography>
            <Typography variant="body1" paragraph>
              Practice writing Japanese kanji characters with stroke order guidance.
              Select a word group to begin practicing.
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
                onChange={(event) => {
                  const newGroupId = event.target.value;
                  setSelectedGroupId(newGroupId);
                  if (newGroupId) {
                    navigate(`/kanji-writing/${newGroupId}`);
                  }
                }}
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
                  <MenuItem key={group.id} value={group.id.toString()}>
                    {group.category}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </CardContent>
        </Card>
      </Box>
    );
  }

  if (!currentWord) {
    return (
      <Box p={3}>
        <Alert severity="info">
          {error || 'No words available in this group. Please select another group.'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Card sx={{ bgcolor: '#f9fafb' }}>
        <CardContent>
          <Typography variant="h4" gutterBottom>
            Kanji Writing Practice
          </Typography>
          <Typography variant="body1" paragraph>
            Practice writing Japanese kanji characters with stroke order guidance.
            Note: Stroke order data is not available yet. This feature will be added in a future update.
          </Typography>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 mb-8">
            <div className="mb-4">
              <Typography variant="h6" gutterBottom>Current Word</Typography>
              <div className="flex flex-col items-center mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Typography variant="subtitle1" color="textSecondary">Kanji:</Typography>
                  <Typography variant="h2" className="text-gray-900 dark:text-white">{currentWord.kanji}</Typography>
                </div>
                <div className="flex items-center gap-2 mb-1">
                  <Typography variant="subtitle1" color="textSecondary">Romaji:</Typography>
                  <Typography variant="h5" className="text-gray-900 dark:text-white">{currentWord.romaji}</Typography>
                </div>
                <div className="flex items-center gap-2">
                  <Typography variant="subtitle1" color="textSecondary">English:</Typography>
                  <Typography variant="h6" className="text-gray-900 dark:text-white">{currentWord.english}</Typography>
                </div>
              </div>
            </div>

            <div className="flex flex-col items-center mb-4">
              <Typography variant="subtitle1" gutterBottom className="text-center">
                Practice writing the kanji above
              </Typography>
              <div className="flex justify-center w-full">
                <canvas
                  ref={canvasRef}
                  width={300}
                  height={300}
                  className="border border-gray-300 dark:border-gray-600 rounded-lg mb-4 bg-white dark:bg-gray-800"
                  onMouseDown={startDrawing}
                  onMouseMove={draw}
                  onMouseUp={stopDrawing}
                  onMouseLeave={stopDrawing}
                  onTouchStart={startDrawing}
                  onTouchMove={draw}
                  onTouchEnd={stopDrawing}
                />
              </div>
            </div>

            <div className="flex justify-center space-x-4 mb-4">
              <Button variant="outlined" onClick={clearCanvas}>Clear</Button>
              <Button variant="contained" onClick={nextWord}>Next Word</Button>
            </div>

            {feedback && (
              <Alert severity="info" sx={{ mt: 2 }}>
                {feedback}
              </Alert>
            )}
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
            <Typography variant="h6" gutterBottom>Progress</Typography>
            <Typography variant="body1">
              Word {currentWordIndex + 1} of {words.length}
            </Typography>
            <Box sx={{ width: '100%', bgcolor: 'background.paper', mt: 2 }}>
              <Box
                sx={{
                  width: `${((currentWordIndex + 1) / words.length) * 100}%`,
                  height: 8,
                  bgcolor: 'primary.main',
                  borderRadius: 1,
                }}
              />
            </Box>
            <Typography variant="body1" sx={{ mt: 2 }}>
              Score: {score}
            </Typography>
          </div>
        </CardContent>
      </Card>
    </Box>
  );
};

export default KanjiWritingPage; 