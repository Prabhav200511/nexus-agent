export default function ExecutionTrace({ logs }: any) {
  return (
    <div className="bg-base-200 p-4 rounded h-full overflow-auto">
      <h2 className="font-bold mb-2">Execution Trace</h2>

      {logs.map((log: any, i: number) => (
        <div key={i} className="text-sm">
          {JSON.stringify(log)}
        </div>
      ))}
    </div>
  )
}