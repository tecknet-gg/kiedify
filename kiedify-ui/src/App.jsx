import {useState, useEffect} from 'react'

const URL = "https://api.tecknet.dev"

function App() {
    const [artists, setArtists] = useState([])
    const [selectedArtist, setSelectedArtist] = useState('')
    const [promptText, setPromptText] = useState('')
    const [loading, setLoading] = useState(false)
    const [audioUrl, setAudioUrl] = useState(null)
    const [error, setError] = useState(null)
    const [statusMessage, setStatusMessage] = seState('')

    useEffect(() => {
        fetch(`${URL}/artists`)
            .then((res) => {
                if (!res.ok) throw new Error("Failed to fetch artists")
                return res.json()
            })
            .then((data) => {
                const list = data.artists || data
                setArtists(list)
                if (list.length > 0) setSelectedArtist(list[0].name)
            })
            .catch((err) => {
                console.error("API Error:", err)
                setError("Could not connect to the API.")
            })

    }, [])


    const pollTaskStatus = async (taskId) => {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`${URL}/status/${taskId}`)
                if (!res.ok) throw new Error("Failed to check task status")
                const data = await res.json()

                if (data.status == "completed") {
                    clearInterval(interval)
                    setAudioUrl(`${URL}/download/${taskId}`)
                    setLoading(false)
                    setStatusMessage('')
                } else if (data.status == "failed") {
                    clearInterval(interval)
                    setError(data.error || "Audio generation failed.")
                    setLoading(false)
                    setStatusMessage('')
                } else {
                    setStatusMessage(`Status: ${data.status} - ${data.queuePosition}`)
                }
            } catch (err) {
                clearInterval(interval)
                console.error("Polling Error:", err)
                setError("Error checking audio task status.")
                setLoading(false)
            }

        }, 2000)
    }
}