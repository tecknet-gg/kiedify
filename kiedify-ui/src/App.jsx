/** @jsxImportSource theme-ui */

import { useState } from 'react'
import { Box, Container, Card, Input, Button, Flex, IconButton } from 'theme-ui'
import Icon from '@hackclub/icons'

const URL = 'https://api.tecknet.dev'

export default function App() {
    const [promptText, setPromptText] = useState('')
    const [selectedArtist, setSelectedArtist] = useState('Red Hot Chili Peppers')
    const [selectedMode, setSlectedMode] = useState('basic')
    const [isLoading, setIsLoading] = useState(false)

    const [messages, setMessages] = useState([

    ])

    const pollTaskStatus = async (taskId, userPrompt) => {
        try {
            const res = await fetch(`${URL}/status/${taskId}`)
            const data = await res.json()

            if (data.status === 'completed') {
                const audioUrl = await fetch (`${URL}/download/${taskId}`)

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
                setMessage((prev) =>
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
            {id: systemtaskId, taskid: systemTaskId, esnder: 'system', text: 'Queuing'},

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
                {id: Date.now(), sender: 'system', text: 'Failed to connect to API - ${error.message}'}
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
            </Container>
        </Box>
    )
}