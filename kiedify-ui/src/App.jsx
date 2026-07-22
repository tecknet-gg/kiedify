import {useState, useEffect} from 'react'

function App() {
  const [artists, setArtists] = useState([])
  const [loading, setLoading] = useState(true)


useEffect(() => {
    fetch('http://localhost:8000')
      .then((res) => res.json())
      .then((data) => {
        setArtists(data.artists || data)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Error fetching artists:', err)
        setLoading(false)
      })
  }, [])

  return (
      <div style = {{ padding: "2rem", fontFamily: "sans-serif"}}>
        <h1>Kiedify</h1>
        <p>MusicTTS Frontend</p>
      </div>
  )
}

export default App


