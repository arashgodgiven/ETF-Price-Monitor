import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from "recharts";

function HoldingsChart({ holdings }) {
  return (
    <div>
      <h3>Top 5 Holdings</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={holdings}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="holding_size" fill="#82ca9d" name="Holding Size" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default HoldingsChart;