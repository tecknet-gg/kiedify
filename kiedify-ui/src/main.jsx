import React from "react"
import ReactDOM from "react-dom/client"
import {ThemeUIProvider} from "theme-ui" //changed import non-deprecated class
import theme from "@hackclub/theme"
import App_old from "./App.jsx"

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <ThemeUIProvider theme={theme}>
            <App_old/>
        </ThemeUIProvider>
    </React.StrictMode>
)