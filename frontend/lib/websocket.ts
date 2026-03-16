export function connectWebSocket(onMessage: (data: any) => void) {
  const ws = new WebSocket("ws://localhost:8000/ws")

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    onMessage(data)
  }

  ws.onopen = () => console.log("WebSocket connected")
  ws.onerror = (e) => console.error("WebSocket error", e)
  ws.onclose = () => console.log("WebSocket closed")

  return ws
}