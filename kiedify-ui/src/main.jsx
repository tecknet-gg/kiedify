import React from "react"
import ReactDOM from "react-dom/client"
import { ThemeProvider } from "theme-ui"
import theme from "@hackclub/theme"
import App from "./App.jsx"

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <ThemeProvider theme={theme}>
            <App/>
        </ThemeProvider>
    </React.StrictMode>
)