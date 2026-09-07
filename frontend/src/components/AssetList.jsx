export default function AssetList({ assets, onEdit, onDelete }) {
  if (assets.length === 0) {
    return <p className="empty">No assets yet. Add one to get started.</p>
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>IP address</th>
            <th>Owner</th>
            <th className="numeric">Findings</th>
            <th aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {assets.map((asset) => (
            <tr key={asset.id}>
              <td>
                <strong>{asset.name}</strong>
                {asset.description && <div className="muted">{asset.description}</div>}
              </td>
              <td>
                <span className="tag">{asset.asset_type}</span>
              </td>
              <td className="mono">{asset.ip_address || '—'}</td>
              <td>{asset.owner || '—'}</td>
              <td className="numeric">{asset.vulnerability_count}</td>
              <td className="actions">
                <button onClick={() => onEdit(asset)}>Edit</button>
                <button className="danger" onClick={() => onDelete(asset)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
