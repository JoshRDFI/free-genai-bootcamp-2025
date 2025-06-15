import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { Navigation } from './components/Navigation';
import StudyActivitiesPage from './pages/StudyActivitiesPage';
import StudyActivityShowPage from './pages/StudyActivityShowPage';
import WordGroupsPage from './pages/WordGroupsPage';
import WordGroupDetailPage from './pages/WordGroupDetailPage';
import { Quiz } from './components/Quiz';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Router>
        <div className="min-h-screen">
          <Navigation />
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<StudyActivitiesPage />} />
              <Route path="/study-activities/:id" element={<StudyActivityShowPage />} />
              <Route path="/word-groups" element={<WordGroupsPage />} />
              <Route path="/word-groups/:groupId" element={<WordGroupDetailPage />} />
              <Route path="/quiz/select" element={<Quiz />} />
              <Route path="/quiz/:groupId" element={<Quiz />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App; 