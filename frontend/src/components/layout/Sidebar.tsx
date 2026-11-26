
export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-icon">IR</div>
        <div>
          <strong>InsureRate</strong>
          <span>Intelligent Rating</span>
        </div>
      </div>

      <div className="sidebar-label">WORKSPACE</div>

      <div className="nav-item active">
        ◈ <span>Policy Analysis</span>
      </div>

      <div className="sidebar-bottom">
        <span className="status-dot" />
        FastAPI backend
      </div>
    </aside>
  );
}
