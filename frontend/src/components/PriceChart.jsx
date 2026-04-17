import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Brush
} from "recharts";

function PriceChart({ priceData }) {
  const data = priceData.dates.map((date, i) => ({
    date,
    price: priceData.prices[i],
  }));

  return (
    <div>
      <h3>ETF Price Over Time</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={40} />
          <YAxis />
          <Tooltip />
          <Brush dataKey="date" height={25} stroke="#8884d8" />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#8884d8"
            dot={false}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PriceChart;