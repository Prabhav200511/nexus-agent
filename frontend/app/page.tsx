"use client"

import { useEffect, useState } from "react"
import TaskInput from "../components/TaskInput"
import ExecutionTrace from "../components/ExecutionTrace"
import ToolPanel from "../components/ToolPanel"
import { connectWebSocket } from "../lib/websocket"

export default function Home() {
  const [logs, setLogs] = useState<any[]>([])
  const [tools, setTools] = useState<string[]>([])

  useEffect(() => {
    const ws = connectWebSocket((data) => {
      setLogs((prev) => [...prev, data])
    })

    return () => ws.close()
  }, [])

  return (
    <div className="flex h-screen">

      <div className="flex-1 p-6 space-y-4">

        <TaskInput onTask={() => {}} />

        <ExecutionTrace logs={logs} />

        <ToolPanel tools={tools} />

      </div>

    </div>
  )
}