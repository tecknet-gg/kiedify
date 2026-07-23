import {useState, useEffect} from 'react'

const URL = "https://api.tecknet.dev"

function App() {
    const [artists, setArtists] = useState([])
    const [selectedArtist, setSelectedArtist] = useState('')
    const [promptText, setPromptText] = useState('')
    const [loading, setLoading] = useState(false)
    const [audioUrl, setAudioUrl] = useState(null)
    const [error, setError] = useState(null)
    const [statusMessage, setStatusMessage] = useState('')

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


    const handleGenerate = async (e) => {
        e.preventDefault()
        if (!promptText.trim()) return

        setLoading(true)
        setError(null)
        setAudioUrl(null)
        setStatusMessage("Queuing job.")

        try {
            const res = await fetch(`${URL}/generate`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    artist: selectedArtist,
                    text: promptText,
                    mode: "basic",
                    patching: true
                })
            })
            if (!res.ok) throw new Error("Failed to queue generation")

            const data = await res.json()
            pollTaskStat(data.taskId)

        } catch (err) {
            console.error("Generation Error:", err)
            setError("Failed to start audio generation")
            setLoading(false)
            setStatusMessage("")
        }
    }


        return (
            <div style={{maxWidth: "600px", margin: "3rem auto", fontFamily: "sans-serif"}}>
                <h1> Kiedify </h1>

                <form onSubmit={handleGenerate}>
                    <div style={{marginBottom: "1rem"}}>
                        <label style={{display: "block", fontWeight: "bold"}}> Select Artist: </label>
                        <select
                            value={selectedArtist}
                            onChange={(e) => setSelectedArtist(e.target.value)}
                            style={{width: "100%", padding: "8px", marginTop: "4px"}}
                        >
                            {artists.map((artistObj, idx) => (
                                <option key={idx} value={artistObj.name}>
                                    {artistObj.name} ({artistObj.gender})
                                </option>
                            ))}
                        </select>
                    </div>
                    {/* Prompt Input */}
                    <div style={{marginBottom: "1rem"}}>
                        <label style={{display: "block", fontWeight: "bold"}}>Script / Text Prompt:</label>
                        <textarea
                            rows="4"
                            value={promptText}
                            onChange={(e) => setPromptText(e.target.value)}
                            placeholder="Type your text here..."
                            style={{width: "100%", padding: "8px", marginTop: "4px"}}
                            required
                        />
                    </div>

                    <button type="submit" disabled={loading} style={{padding: "10px 20px", cursor: "pointer"}}>
                        {loading ? "Processing..." : "Generate Audio"}
                    </button>
                </form>

                {/*Status*/}
                {statusMessage && <p style={{color: "#0284c7", marginTop: "1rem"}}>{statusMessage}</p>}

                {/* Audio Player*/}
                {audioUrl && (
                    <div style={{marginTop: "2rem"}}>
                        <h3>Generated Audio:</h3>
                        <audio controls src={audioUrl} style={{width: "100%"}}/>
                    </div>
                )}
            </div>
        )
}
export default App
