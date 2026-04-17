function ETFTable({ constituents }) {
  return (
    <div>
      <h3>Constituents</h3>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ backgroundColor: "#f0f0f0" }}>
            <th style={th}>Name</th>
            <th style={th}>Weight</th>
            <th style={th}>Latest Close Price</th>
          </tr>
        </thead>
        <tbody>
          {constituents.map((c) => (
            <tr key={c.name}>
              <td style={td}>{c.name}</td>
              <td style={td}>{(c.weight * 100).toFixed(2)}%</td>
              <td style={td}>${c.latest_price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const th = { padding: "10px", border: "1px solid #ccc", textAlign: "left" };
const td = { padding: "10px", border: "1px solid #ccc" };

export default ETFTable;