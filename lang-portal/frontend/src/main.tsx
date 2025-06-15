import React from "react";
import ReactDOM from "react-dom/client";
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import App from "./app";
import "./index.css";

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
  typography: {
    h1: {
      color: '#374151',
    },
    h2: {
      color: '#374151',
    },
    h3: {
      color: '#374151',
    },
    h4: {
      color: '#374151',
    },
    h5: {
      color: '#374151',
    },
    h6: {
      color: '#374151',
    },
    body1: {
      color: '#374151',
    },
    body2: {
      color: '#374151',
    },
    subtitle1: {
      color: '#374151',
    },
    subtitle2: {
      color: '#374151',
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
); 