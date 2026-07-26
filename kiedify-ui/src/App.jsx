/** @jsxImportSource theme-ui */

import { useState, useEffect } from 'react'
import { Box, Container, Card, Input, Button, Flex, IconButton, Heading, Text, Select } from 'theme-ui'
import Icon from '@hackclub/icons'

const URL = 'https://api.tecknet.dev'
const DEFAULT_ARTIST = [
    {name: 'Red Hot chili Peppers', gender: 'male'}
]


export default function App() {
    const [promptText, setPromptText] = useState('')
    const [selectedArtist, setSelectedArtist] = useState('Red Hot Chili Peppers')
    const [selectedMode, setSelectedMode] = useState('basic')
    const [isLoading, setIsLoading] = useState(false)
    const [artists, setArtists] = useState(DEFAULT_ARTIST)

    const [messages, setMessages] = useState([
        {id: 'welcome', sender: 'system', text: 'Welcome to Kiedify, pick an artist mess around with the settings and input some text!'}
    ])

    useEffect(() => {
        async function fetchArtists() {
            try {
                const res = await fetch(`${URL}/artists`)
                if (res.ok) {
                    const data = await res.json()
                    if (data.artists && data.artists.length>0) {
                        setArtists(data.artists)
                        setSelectedArtist(data.artists[0].name)
                    }
                }
            } catch (err) {
                console.warn("Couldn't fetch artists from API")
            }
        }
        fetchArtists()
    }, [])

    const pollTaskStatus = async (taskId, userPrompt) => {
        try {
            const res = await fetch(`${URL}/status/${taskId}`)
            const data = await res.json()

            if (data.status === 'completed') {
                const audioUrl= `${URL}/download/${taskId}`

                setMessages((prev) =>
                    prev.map((msg) =>
                        msg.taskId === taskId
                        ? {
                                ...msg,
                                status: 'completed',
                                text: `Generated track for ${userPrompt}`,
                                audioUrl: audioUrl
                            }
                            : msg
                    )
                )
                setIsLoading(false)
            } else if (data.status === 'failed') {
                setMessages((prev) =>
                    prev.map((msg) =>
                        msg.taskId === taskId
                            ? {...msg, status: 'failed', text: 'Generation failed'}
                            :msg
                    )
                )
                setIsLoading(false)
            } else {
                const queueInfo = data.queuePosition ? `(Queue position: ${data.queuePosition})`: ''
                setMessages((prev) =>
                    prev.map((msg) =>
                        msg.taskId === taskId
                            ? {...msg, text: `Synthesising audio ${queueInfo}`}
                            :msg
                    )
                )
                setTimeout(() => pollTaskStatus(taskId, userPrompt), 2000)
            }
        } catch (error) {
            console.error('Error polling status', error)
            setIsLoading(false)
        }
    }

    const handleSend = async (e) => {
        e?.preventDefault()
        if (!promptText.trim() || isLoading) return

        const userText = promptText
        const userMsgId = Date.now()
        const systemTaskId = `task-${Date.now()}`

        setMessages((prev) => [
            ...prev,
            {id: userMsgId, sender: 'user', text: userText},
            {id: systemTaskId, taskId: systemTaskId, sender: 'system', text: 'Queuing'},

        ])

        setPromptText('')
        setIsLoading(true)

        try {
            const res = await fetch(`${URL}/generate`,{
                method: 'POST',
                headers: {'Content-type': 'application/json'},
                body: JSON.stringify({
                    artist: selectedArtist,
                    text: userText,
                    mode: selectedMode,
                    patching: true,
                    fuzzy: true
                })
            })

            if (!res.ok) {
                throw new Error(`HTTP Error ${res.status}`)
            }

            const data = await res.json()

            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === systemTaskId ? {...msg, taskId: data.taskId} : msg
                )
            )
            pollTaskStatus(data.taskId, userText)
        } catch (error) {
            setMessages((prev) => [
                ...prev,
                {id: Date.now(), sender: 'system', text: `Failed to connect to API - ${error.message}`}
            ])
            setIsLoading(false)
        }
    }

    return (
        <Box
            sx={{
                minHeight: '100vh',
                bg: 'darker',
                backgroundImage: 'linear-gradient(135deg, hsl(225, 70%, 5%) 0%, hsl(220, 60%, 3%) 50%, hsl(210, 50%, 4%) 100%)',
                backgroundAttachment: 'fixed',
                display: 'flex',
                flexDirection: 'column',
                p: [3,4]
            }}
        >
            <Container sx={{maxWidth: '640px', width: '100%'}} >

                <Flex sx={{ alignItems: 'center', mb: 3, gap:2}}>
                    <Icon glyph="music" size={36} sx={{color: 'red'}}/>
                    <Heading
                        as='h1'
                        sx={{
                            color: 'white',
                            fontSize: [4,5],
                            fontFamily: 'heading',
                            fontWeight: 'bold'
                        }}
                    >
                        Kiedify
                    </Heading>
                </Flex>

                <Card
                    sx={{
                        bg: '#0f172a',
                        borderRadius: 'extra',
                        p: 4,
                        minHeight: '420px',
                        maxHeight: '520px',
                        overflowY: 'auto',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 3,
                        border: '1px solid',
                        borderColor: '#1e293b'
                    }}
                >
                    {messages.map((msg) => (
                        <Flex
                            key={msg.id}
                            sx={{
                                flexDirection:'column',
                                alignItems: msg.sender === 'user' ? 'flex-end': 'flex-start'
                            }}
                        >
                            <Box
                                sx={{
                                    bg: msg.sender === 'user' ? 'red': '#1e293b',
                                    color: 'white',
                                    px: 3,
                                    py: 2,
                                    borderRadius: 'large',
                                    maxWidth: '85%',
                                    fontSize: 2,
                                    fontWeight: 'medium',
                                    border: msg.sender === 'user' ? 'none': '1px solid #334155'
                                }}
                            >
                                <Text>{msg.text}</Text>
                                {msg.audioUrl && (
                                    <Box sx={{mt:2}} >
                                        <audio
                                            controls
                                            src={msg.audioUrl}
                                            style={{width: '100%', borderRadius: '8px', outline: 'none'}}
                                        />
                                    </Box>
                                )}
                            </Box>
                        </Flex>
                    ))}
                </Card>

                <Box
                    as='form'
                    onSubmit={handleSend}
                    sx={{
                        mt: 3,
                        bg: '#0f172a',
                        borderRadius: 'circle',
                        p: 2,
                        px: 3,
                        display: 'flex',
                        alignItems: 'center',
                        border: '1px solid',
                        borderColor: '#1e293b',
                        '&:focus-within': {borderColor: 'red'}
                    }}
                >
                    <Input
                        value={promptText}
                        onChange={(e) => setPromptText(e.target.value)}
                        placeholder={isLoading ? "Generating track..": "Type lyrics to synthesise..."}
                        disabled={isLoading}
                        sx={{
                             border: 'none',
                            outline: 'none',
                            color: 'white',
                            fontSize: 2,
                            px: 2,
                            '&:focus': {outline: 'none', boxShadow: 'none'}
                        }}
                    />
                    <IconButton
                        type='submit'
                        disabled={isLoading}
                        sx={{
                            bg: isLoading ? '#1e293b': 'red',
                            color: 'white',
                            borderRadius: 'circle',
                            cursor: isLoading? 'not-allowed': 'pointer',
                            p: 2,
                            '&:hover': {bg: isLoading ? '#1e293b': 'red'}
                        }}
                    >
                        <Icon glyph="send" size={24}/>
                    </IconButton>
                </Box>

                <Flex sx={{ mt: 3, gap: 2, flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center'}}>
                    <Select
                        value={selectedArtist}
                        onChange={(e) => setSelectedArtist(e.target.value)}
                        sx={{
                            bg: '#0f172a',
                            color: 'red',
                            border: '1px solid',
                            borderColor: 'red',
                            borderRadius: 'pill',
                            px: 3,
                            py: 1,
                            fontSize: 1,
                            fontWeight: 'bold',
                            cursor: 'pointer',
                            width: 'auto'
                        }}
                    >
                        {artists.map((artist) => (
                            <option key={artist.name} value = {artist.name}>
                                {artist.name} ({artist.gender})
                            </option>
                        ))}
                    </Select>
                </Flex>

            </Container>
        </Box>
    )
}