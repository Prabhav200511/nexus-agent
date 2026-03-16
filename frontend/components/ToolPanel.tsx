export default function ToolPanel({ tools }: any) {
  return (
    <div className="bg-base-200 p-4 rounded">
      <h2 className="font-bold">Tools</h2>

      {tools.map((tool: string, i: number) => (
        <div key={i} className="badge badge-outline mr-2">
          {tool}
        </div>
      ))}
    </div>
  )
}