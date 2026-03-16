"use client"

import { useState } from "react"

export default function TaskInput({ onTask }: any) {
  const [prompt, setPrompt] = useState("")

  async function submit() {
    const res = await fetch("http://localhost:8000/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    })

    const data = await res.json()

    if (data.success) {
      onTask(data.data)
      setPrompt("")
    }
  }

  return (
    <div className="flex gap-2 p-4">
      <input
        className="input input-bordered w-full"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Enter task..."
      />

      <button className="btn btn-primary" onClick={submit}>
        Run
      </button>
    </div>
  )
}