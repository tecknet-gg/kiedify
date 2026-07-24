/** @jsxImportSource theme-ui */

import { useState } from 'react'
import { Box, Container, Card, Input, Button, Flex, IconButton } from 'theme-ui'
import Icon from '@hackclub/icons'

export default function App() {
    const [promptText, setPromptText] = useState('')
    const [selectedArtist, setSelectedArtist] = useState('Red Hot Chili Peppers')
    const [selectedMode, setSlectedMode] = useState('basic')

    const [messages, setMessages] = useState([

    ])

    const handleSend = (e) => {
        e?.preventDefault()
        if (!promptText.trim()) return
        setMessages((prev) => [
            ...prev,
            {id: Date.now(), sender: 'user', text: promptText },
        ])
        setPromptText('')
    }

    return (
        <Box
            sx={{
                minHeight: '100vh',
                bg: '#17171d',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justify: 'center',
                p: 3
            }}
        ></Box>
    )
}