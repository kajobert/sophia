import React, { useState, useEffect, useRef } from 'react';

const TaskRunner = () => {
    const [prompt, setPrompt] = useState('');
    const [taskId, setTaskId] = useState(null);
    const [steps, setSteps] = useState([]);
    const [feedback, setFeedback] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const ws = useRef(null);

    useEffect(() => {
        if (!taskId) return;

        const connectWebSocket = () => {
            // Use relative path for WebSocket connection
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsHost = window.location.host;
            ws.current = new WebSocket(`${wsProtocol}//${wsHost}/api/v1/tasks/${taskId}/ws`);

            ws.current.onopen = () => {
                console.log('WebSocket connected');
            };

            ws.current.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('Received data:', data);
                if (data.type === 'step_update') {
                    setSteps(prevSteps => [...prevSteps, data]);
                } else if (data.type === 'plan_feedback') {
                    setFeedback(data.feedback);
                    setIsLoading(false); // Plan finished or failed
                } else if (data.type === 'plan_repaired') {
                    setSteps([]); // Clear steps for the new plan
                    setFeedback(`Plan repaired. New plan: ${JSON.stringify(data.new_plan)}`);
                }
            };

            ws.current.onclose = () => {
                console.log('WebSocket disconnected');
            };

            ws.current.onerror = (error) => {
                console.error('WebSocket error:', error);
                setFeedback('WebSocket connection error.');
                setIsLoading(false);
            };
        };

        connectWebSocket();

        return () => {
            if (ws.current) {
                ws.current.close();
            }
        };
    }, [taskId]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!prompt.trim()) return;

        setIsLoading(true);
        setSteps([]);
        setFeedback('');
        setTaskId(null);

        try {
            const response = await fetch('/api/v1/tasks', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create task');
            }

            const data = await response.json();
            setTaskId(data.task_id);
        } catch (error) {
            console.error('Failed to create task:', error);
            setFeedback(`Error: ${error.message}`);
            setIsLoading(false);
        }
    };

    return (
        <div style={{ fontFamily: 'Arial, sans-serif', padding: '20px' }}>
            <h1>Sophia Task Runner</h1>
            <form onSubmit={handleSubmit}>
                <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="Enter your task prompt here..."
                    rows="5"
                    style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ccc' }}
                    disabled={isLoading}
                />
                <br />
                <button type="submit" disabled={isLoading} style={{ padding: '10px 20px', background: '#1976d2', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', marginTop: '10px' }}>
                    {isLoading ? 'Running...' : 'Run Task'}
                </button>
            </form>
            {taskId && <h2 style={{ marginTop: '20px' }}>Task ID: {taskId}</h2>}
            {isLoading && <p>Waiting for task to start...</p>}
            <div style={{ marginTop: '20px' }}>
                <h3>Progress:</h3>
                <ul style={{ listStyleType: 'none', padding: 0 }}>
                    {steps.map((step, index) => (
                        <li key={index} style={{ background: '#f0f0f0', margin: '5px 0', padding: '10px', borderRadius: '4px' }}>
                            <strong>Step {step.step_id}:</strong> {step.description}
                            <span style={{ marginLeft: '10px', fontWeight: 'bold', color: step.output.status === 'success' ? 'green' : 'red' }}>
                                [{step.output.status.toUpperCase()}]
                            </span>
                            {step.output.status === 'error' && <p style={{ color: 'red', margin: '5px 0 0 0' }}>Error: {step.output.error}</p>}
                        </li>
                    ))}
                </ul>
            </div>
            {feedback && (
                <div style={{ marginTop: '20px', padding: '10px', background: '#e0e0e0', borderRadius: '4px' }}>
                    <h3>Final Feedback:</h3>
                    <p>{feedback}</p>
                </div>
            )}
        </div>
    );
};

export default TaskRunner;
