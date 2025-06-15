import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  InputLabel,
  Select,
  MenuItem,
  FormControl,
} from '@mui/material';

const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState({
    studyReminderTime: '09:00',
    dailyGoal: 50
  });

  useEffect(() => {
    // Load saved settings from localStorage
    const savedSettings = localStorage.getItem('userSettings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
  }, []);

  const handleSettingChange = (key: string, value: string | number) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    localStorage.setItem('userSettings', JSON.stringify(newSettings));
  };

  return (
    <Box p={3}>
      <Card sx={{ bgcolor: '#f9fafb' }}>
        <CardContent>
          <Typography variant="h4" gutterBottom>
            Settings
          </Typography>
          
          <Box sx={{ mt: 3 }}>
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel>Daily Word Goal</InputLabel>
              <Select
                value={settings.dailyGoal}
                onChange={(e) => handleSettingChange('dailyGoal', e.target.value)}
                label="Daily Word Goal"
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
                <MenuItem value={25}>25 words</MenuItem>
                <MenuItem value={50}>50 words</MenuItem>
                <MenuItem value={75}>75 words</MenuItem>
                <MenuItem value={100}>100 words</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Study Reminder Time</InputLabel>
              <Select
                value={settings.studyReminderTime}
                onChange={(e) => handleSettingChange('studyReminderTime', e.target.value)}
                label="Study Reminder Time"
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
                <MenuItem value="08:00">8:00 AM</MenuItem>
                <MenuItem value="09:00">9:00 AM</MenuItem>
                <MenuItem value="10:00">10:00 AM</MenuItem>
                <MenuItem value="11:00">11:00 AM</MenuItem>
                <MenuItem value="12:00">12:00 PM</MenuItem>
                <MenuItem value="13:00">1:00 PM</MenuItem>
                <MenuItem value="14:00">2:00 PM</MenuItem>
                <MenuItem value="15:00">3:00 PM</MenuItem>
                <MenuItem value="16:00">4:00 PM</MenuItem>
                <MenuItem value="17:00">5:00 PM</MenuItem>
                <MenuItem value="18:00">6:00 PM</MenuItem>
                <MenuItem value="19:00">7:00 PM</MenuItem>
                <MenuItem value="20:00">8:00 PM</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SettingsPage;