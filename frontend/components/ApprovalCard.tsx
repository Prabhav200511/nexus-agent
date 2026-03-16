export default function ApprovalCard({ action, onApprove, onReject }: any) {
  return (
    <div className="card bg-base-200 p-4">
      <h3 className="font-bold">Approval Required</h3>

      <p>{action}</p>

      <div className="flex gap-2 mt-2">
        <button className="btn btn-success" onClick={onApprove}>
          Approve
        </button>

        <button className="btn btn-error" onClick={onReject}>
          Reject
        </button>
      </div>
    </div>
  )
}