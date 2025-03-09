import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useDropzone } from "react-dropzone";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
    Box,
    Paper,
    TextField,
    Button,
    Avatar,
    CircularProgress,
    IconButton,
    Typography,
    List,
    ListItem,
    ListItemText,
    Snackbar,
    Alert,
} from "@mui/material";
import { Send, CloudUpload, Person, SmartToy } from "@mui/icons-material";

function App() {
    const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
    const [input, setInput] = useState("");
    const [uploading, setUploading] = useState(false);
    const [loading, setLoading] = useState(false);
    const [files, setFiles] = useState<File[]>([]);
    const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: "success" | "error" }>({
        open: false,
        message: "",
        severity: "success",
    });
    const chatEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const { getRootProps, getInputProps } = useDropzone({
        accept: { "application/pdf": [".pdf"] },
        onDrop: (acceptedFiles) => {
            setFiles((prevFiles) => [...prevFiles, ...acceptedFiles]);
        },
    });

    const startNewConversation = async () => {
        try {
            const response = await fetch("http://localhost:8000/start_conversation");
            const data = await response.json();
            setConversationId(data.conversation_id);
            setMessages([]);
            setUploadedFiles([]);
            setFiles([]);
            setSnackbar({ open: true, message: `New conversation started with ID: ${data.conversation_id}`, severity: "success" });
        } catch (error) {
            console.error("Error starting conversation:", error);
            setSnackbar({ open: true, message: "Failed to start a new conversation.", severity: "error" });
        }
    };

    const uploadFiles = async () => {
        if (!conversationId) {
            setSnackbar({ open: true, message: "Please start a conversation first!", severity: "error" });
            return;
        }
        if (files.length === 0) return;
        setUploading(true);
        const formData = new FormData();
        files.forEach((file) => formData.append("files", file));

        try {
            const response = await axios.post(
                `http://localhost:8000/upload?conversation_id=${conversationId}`,
                formData
            );
            console.log("Upload response:", response);
            if (response.status === 200 && response.data.message) {
                setSnackbar({ open: true, message: "Upload successful!", severity: "success" });
                setUploadedFiles((prev) => [...prev, ...files.map((file) => file.name)]);
                setFiles([]);
            } else {
                setSnackbar({ open: true, message: "Upload failed. Server did not return a success message.", severity: "error" });
            }
        } catch (error) {
            console.error("Upload failed:", error);
            setSnackbar({ open: true, message: "Upload failed. Please try again.", severity: "error" });
        }
        setUploading(false);
    };

    const sendMessage = async () => {
        if (!conversationId) {
            setSnackbar({ open: true, message: "Please start a conversation first!", severity: "error" });
            return;
        }
        if (!input.trim() || loading) return;
        setMessages((prev) => [...prev, { role: "user", content: input }]);
        setInput("");
        setLoading(true);

        setMessages((prev) => [...prev, { role: "assistant", content: "🤔 Thinking..." }]);

        try {
            const response = await fetch(
                `http://localhost:8000/chat?conversation_id=${conversationId}&query=${encodeURIComponent(input)}`
            );
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            setMessages((prev) =>
                prev.slice(0, -1).concat({ role: "assistant", content: data.response })
            );
        } catch (error) {
            console.error("Error fetching response:", error);
            setMessages((prev) =>
                prev.slice(0, -1).concat({ role: "assistant", content: "Sorry, an error occurred. Please try again." })
            );
        }
        setLoading(false);
    };

    const handleKeyPress = (event: React.KeyboardEvent) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    };

    const handleSnackbarClose = () => {
        setSnackbar((prev) => ({ ...prev, open: false }));
    };

    return (
        <Box
            sx={{
                bgcolor: "#1a1a1a",
                color: "white",
                position: "fixed",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                p: 4,
                display: "flex",
                flexDirection: "column",
                boxSizing: "border-box",
                m: 0,
                overflow: "hidden",
            }}
        >
            <Typography
                variant="h4"
                sx={{
                    textAlign: "center",
                    mb: 3,
                    fontWeight: "bold",
                    color: "#00e676",
                }}
            >
                💬 Legal Chatbot
            </Typography>

            <Button
                variant="contained"
                onClick={startNewConversation}
                sx={{
                    mb: 3,
                    bgcolor: "#0288d1",
                    "&:hover": { bgcolor: "#0277bd" },
                    borderRadius: "8px",
                    textTransform: "none",
                }}
            >
                Start New Conversation
            </Button>

            <Box sx={{ display: "flex", flex: 1, gap: 3, height: "calc(100% - 140px)" }}>
                {/* Cột danh sách file PDF */}
                <Paper
                    sx={{
                        width: "25%",
                        p: 2,
                        bgcolor: "#2c2c2c",
                        borderRadius: "12px",
                        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.2)",
                        overflowY: "auto",
                    }}
                >
                    <Typography variant="h6" sx={{ mb: 2, color: "#00e676" }}>
                        Uploaded PDFs
                    </Typography>
                    <List>
                        {uploadedFiles.length > 0 ? (
                            uploadedFiles.map((fileName, index) => (
                                <ListItem key={index} sx={{ py: 1 }}>
                                    <ListItemText primary={fileName} sx={{ color: "#bdbdbd" }} />
                                </ListItem>
                            ))
                        ) : (
                            <Typography sx={{ color: "#616161" }}>No files uploaded yet.</Typography>
                        )}
                    </List>
                </Paper>

                {/* Phần chính: Upload và Chat */}
                <Box sx={{ flex: 1, display: "flex", flexDirection: "column", gap: 3 }}>
                    {/* File Upload Section */}
                    <Paper
                        {...getRootProps()}
                        sx={{
                            p: 3,
                            textAlign: "center",
                            cursor: "pointer",
                            bgcolor: "#2c2c2c",
                            borderRadius: "12px",
                            border: "2px dashed #616161",
                            transition: "all 0.3s",
                            "&:hover": { borderColor: "#00e676" },
                        }}
                    >
                        <input {...getInputProps()} />
                        <Typography sx={{ color: "#bdbdbd" }}>
                            Drag & drop files here, or click to select files
                        </Typography>
                    </Paper>

                    {files.length > 0 && (
                        <Box
                            sx={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                                p: 2,
                                bgcolor: "#2c2c2c",
                                borderRadius: "12px",
                                boxShadow: "0 4px 12px rgba(0, 0, 0, 0.2)",
                            }}
                        >
                            <Typography sx={{ color: "#bdbdbd" }}>
                                {files.length} file(s) selected
                            </Typography>
                            <Button
                                variant="contained"
                                startIcon={<CloudUpload />}
                                onClick={uploadFiles}
                                disabled={uploading || !conversationId}
                                sx={{
                                    bgcolor: "#00e676",
                                    "&:hover": { bgcolor: "#00c853" },
                                    borderRadius: "8px",
                                    textTransform: "none",
                                }}
                            >
                                {uploading ? <CircularProgress size={20} /> : "Upload"}
                            </Button>
                        </Box>
                    )}

                    {/* Chat Box */}
                    <Paper
                        sx={{
                            flex: 1,
                            overflowY: "auto",
                            p: 3,
                            bgcolor: "#2c2c2c",
                            borderRadius: "12px",
                            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.2)",
                        }}
                    >
                        {messages.map((msg, index) => (
                            <Box
                                key={index}
                                sx={{
                                    display: "flex",
                                    alignItems: "flex-start",
                                    my: 2,
                                    justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
                                }}
                            >
                                {msg.role === "assistant" && (
                                    <Avatar sx={{ bgcolor: "#0288d1", mr: 2, mt: 1 }}>
                                        <SmartToy />
                                    </Avatar>
                                )}
                                <Paper
                                    sx={{
                                        p: 2,
                                        borderRadius: "12px",
                                        maxWidth: "70%",
                                        bgcolor: msg.role === "user" ? "#00e676" : "#424242",
                                        color: "white",
                                        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
                                    }}
                                >
                                    {msg.role === "assistant" ? (
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                            {msg.content}
                                        </ReactMarkdown>
                                    ) : (
                                        <Typography>{msg.content}</Typography>
                                    )}
                                </Paper>
                                {msg.role === "user" && (
                                    <Avatar sx={{ bgcolor: "#00c853", ml: 2, mt: 1 }}>
                                        <Person />
                                    </Avatar>
                                )}
                            </Box>
                        ))}
                        <div ref={chatEndRef}></div>
                    </Paper>
                </Box>
            </Box>

            {/* Chat Input */}
            <Box sx={{ display: "flex", alignItems: "center", mt: 3 }}>
                <TextField
                    fullWidth
                    variant="outlined"
                    placeholder="Ask a legal question..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    sx={{
                        bgcolor: "#2c2c2c",
                        borderRadius: "12px",
                        "& .MuiOutlinedInput-root": {
                            color: "white",
                            "& fieldset": { borderColor: "#616161" },
                            "&:hover fieldset": { borderColor: "#00e676" },
                            "&.Mui-focused fieldset": { borderColor: "#00e676" },
                            "& .MuiInputBase-input::placeholder": {
                                color: "#bdbdbd",
                                opacity: 1,
                            },
                        },
                    }}
                    disabled={loading || !conversationId}
                />
                <IconButton
                    color="primary"
                    onClick={sendMessage}
                    sx={{ ml: 2, bgcolor: "#00e676", "&:hover": { bgcolor: "#00c853" } }}
                    disabled={loading || !conversationId}
                >
                    {loading ? <CircularProgress size={24} /> : <Send />}
                </IconButton>
            </Box>

            {/* Snackbar thông báo */}
            <Snackbar
                open={snackbar.open}
                autoHideDuration={3000}
                onClose={handleSnackbarClose}
                anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
            >
                <Alert onClose={handleSnackbarClose} severity={snackbar.severity} sx={{ width: "100%" }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Box>
    );
}

export default App;