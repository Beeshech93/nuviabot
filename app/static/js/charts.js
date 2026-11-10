// NUVIO GROWTH BOT — Interactive Visual Charting Engine (Zero External Dependencies)

class NuvioChart {
  /**
   * Renders an interactive smooth line chart in a given canvas element.
   * @param {HTMLCanvasElement} canvas
   * @param {Array<{date: string, value: number}>} dataPoints
   * @param {Object} options
   */
  static renderLineChart(canvas, dataPoints, options = {}) {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();

    canvas.width = (rect.width || 600) * dpr;
    canvas.height = (rect.height || 220) * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width || 600;
    const height = rect.height || 220;
    const padding = { top: 20, right: 20, bottom: 30, left: 40 };

    ctx.clearRect(0, 0, width, height);

    if (!dataPoints || dataPoints.length === 0) {
      ctx.fillStyle = "#64748b";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("No hay datos suficientes para el período seleccionado", width / 2, height / 2);
      return;
    }

    const values = dataPoints.map(d => d.value);
    const maxVal = Math.max(...values, 10);
    const minVal = 0;

    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    // Draw horizontal grid lines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    ctx.lineWidth = 1;
    const gridLines = 4;
    ctx.fillStyle = "#64748b";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "right";

    for (let i = 0; i <= gridLines; i++) {
      const y = padding.top + (chartH / gridLines) * i;
      const val = Math.round(maxVal - (maxVal / gridLines) * i);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();
      ctx.fillText(val.toLocaleString(), padding.left - 8, y + 3);
    }

    // Compute coordinate points
    const stepX = chartW / (dataPoints.length - 1 || 1);
    const points = dataPoints.map((d, i) => {
      const x = padding.left + i * stepX;
      const y = padding.top + chartH - ((d.value - minVal) / (maxVal - minVal)) * chartH;
      return { x, y, date: d.date, value: d.value };
    });

    // Draw smooth gradient fill under line
    const strokeColor = options.strokeColor || "#6366f1";
    const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
    gradient.addColorStop(0, options.gradientStart || "rgba(99, 102, 241, 0.35)");
    gradient.addColorStop(1, "rgba(99, 102, 241, 0.0)");

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      const xc = (points[i - 1].x + points[i].x) / 2;
      const yc = (points[i - 1].y + points[i].y) / 2;
      ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xc, yc);
    }
    const lastP = points[points.length - 1];
    ctx.lineTo(lastP.x, lastP.y);
    ctx.lineTo(lastP.x, height - padding.bottom);
    ctx.lineTo(points[0].x, height - padding.bottom);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw line
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      const xc = (points[i - 1].x + points[i].x) / 2;
      const yc = (points[i - 1].y + points[i].y) / 2;
      ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xc, yc);
    }
    ctx.lineTo(lastP.x, lastP.y);
    ctx.strokeStyle = strokeColor;
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Draw data points
    points.forEach((p, idx) => {
      if (idx % 2 === 0 || idx === points.length - 1) {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = "#fff";
        ctx.fill();
        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    });

    // Draw X-axis dates
    ctx.fillStyle = "#64748b";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    const dateInterval = Math.max(1, Math.floor(points.length / 5));
    points.forEach((p, idx) => {
      if (idx % dateInterval === 0 || idx === points.length - 1) {
        const dStr = p.date ? p.date.slice(5) : ""; // MM-DD
        ctx.fillText(dStr, p.x, height - 10);
      }
    });
  }

  /**
   * Renders a multi-platform bar chart for comparison.
   * @param {HTMLCanvasElement} canvas
   * @param {Array<{label: string, value: number, color: string}>} bars
   */
  static renderBarChart(canvas, bars) {
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();

    canvas.width = (rect.width || 400) * dpr;
    canvas.height = (rect.height || 200) * dpr;
    ctx.scale(dpr, dpr);

    const width = rect.width || 400;
    const height = rect.height || 200;
    const padding = { top: 20, right: 20, bottom: 30, left: 45 };

    ctx.clearRect(0, 0, width, height);

    if (!bars || bars.length === 0) return;

    const maxVal = Math.max(...bars.map(b => b.value), 10);
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const barWidth = Math.min(48, (chartW / bars.length) * 0.6);
    const stepX = chartW / bars.length;

    bars.forEach((b, i) => {
      const barH = (b.value / maxVal) * chartH;
      const x = padding.left + i * stepX + (stepX - barWidth) / 2;
      const y = padding.top + chartH - barH;

      // Bar fill with rounded top
      ctx.fillStyle = b.color || "#6366f1";
      ctx.beginPath();
      ctx.roundRect(x, y, barWidth, barH, [6, 6, 0, 0]);
      ctx.fill();

      // Value label on top
      ctx.fillStyle = "#f8fafc";
      ctx.font = "bold 10px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(b.value.toLocaleString(), x + barWidth / 2, Math.max(padding.top + 10, y - 6));

      // Category label
      ctx.fillStyle = "#94a3b8";
      ctx.font = "11px sans-serif";
      ctx.fillText(b.label, x + barWidth / 2, height - 10);
    });
  }
}

