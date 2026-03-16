export default function TaskSidebar({ tasks }: any) {
  return (
    <div className="w-64 bg-base-200 p-4">
      <h2 className="font-bold">Task History</h2>

      {tasks.map((t: any) => (
        <div key={t.id} className="border-b py-2">
          {t.prompt}
        </div>
      ))}
    </div>
  )
}